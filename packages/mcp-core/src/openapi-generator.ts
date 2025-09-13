import { z } from "zod";

export interface OpenAPITool {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
}

export interface OpenAPISpec {
  openapi: string;
  info: {
    title: string;
    description: string;
    version: string;
  };
  servers: Array<{
    url: string;
    description: string;
  }>;
  paths: Record<string, any>;
  components: {
    schemas: Record<string, any>;
    securitySchemes?: Record<string, any>;
  };
}

export class OpenAPIGenerator {
  static generateSpec(
    title: string,
    description: string,
    version: string,
    baseUrl: string,
    tools: OpenAPITool[]
  ): OpenAPISpec {
    const spec: OpenAPISpec = {
      openapi: "3.0.0",
      info: {
        title,
        description,
        version,
      },
      servers: [
        {
          url: baseUrl,
          description: "Default server",
        },
      ],
      paths: {},
      components: {
        schemas: {},
      },
    };

    // Add common endpoints
    spec.paths["/health"] = {
      get: {
        summary: "Health check",
        operationId: "getHealth",
        responses: {
          "200": {
            description: "Service is healthy",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    status: { type: "string" },
                    timestamp: { type: "string", format: "date-time" },
                    network: { type: "string" },
                    readOnly: { type: "boolean" },
                  },
                },
              },
            },
          },
        },
      },
    };

    spec.paths["/metrics"] = {
      get: {
        summary: "Prometheus metrics",
        operationId: "getMetrics",
        responses: {
          "200": {
            description: "Metrics in Prometheus format",
            content: {
              "text/plain": {
                schema: {
                  type: "string",
                },
              },
            },
          },
        },
      },
    };

    spec.paths["/tools/list"] = {
      get: {
        summary: "List available tools",
        operationId: "listTools",
        responses: {
          "200": {
            description: "List of available tools",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    tools: {
                      type: "array",
                      items: {
                        type: "object",
                        properties: {
                          name: { type: "string" },
                          description: { type: "string" },
                          inputSchema: { type: "object" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
      },
    };

    // Generate paths for each tool
    tools.forEach((tool) => {
      const pathName = `/tools/${tool.name.replace(/_/g, "-")}`;
      const schemaName = `${tool.name}Input`;

      // Convert Zod schema to OpenAPI schema if possible
      const openApiSchema = this.zodToOpenAPISchema(tool.inputSchema);

      spec.components.schemas[schemaName] = openApiSchema;

      spec.paths[pathName] = {
        post: {
          summary: tool.description,
          operationId: tool.name,
          requestBody: {
            required: true,
            content: {
              "application/json": {
                schema: {
                  $ref: `#/components/schemas/${schemaName}`,
                },
              },
            },
          },
          responses: {
            "200": {
              description: "Successful response",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      success: { type: "boolean" },
                      data: { type: "object" },
                      error: { type: "string" },
                    },
                  },
                },
              },
            },
            "400": {
              description: "Bad request",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      success: { type: "boolean", example: false },
                      error: { type: "string" },
                      details: { type: "array", items: { type: "object" } },
                    },
                  },
                },
              },
            },
            "500": {
              description: "Internal server error",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      success: { type: "boolean", example: false },
                      error: { type: "string" },
                    },
                  },
                },
              },
            },
          },
        },
      };
    });

    return spec;
  }

  private static zodToOpenAPISchema(zodSchema: any): any {
    // Simple conversion for basic types
    const schema: any = { type: "object", properties: {}, required: [] };

    for (const [key, value] of Object.entries(zodSchema)) {
      if (value && typeof value === "object") {
        const fieldSchema: any = {};

        // Try to infer type from Zod schema structure
        if ((value as any)._def) {
          const def = (value as any)._def;
          switch (def.typeName) {
            case "ZodString":
              fieldSchema.type = "string";
              if (def.checks) {
                def.checks.forEach((check: any) => {
                  if (check.kind === "min") fieldSchema.minLength = check.value;
                  if (check.kind === "max") fieldSchema.maxLength = check.value;
                });
              }
              break;
            case "ZodNumber":
              fieldSchema.type = "number";
              if (def.checks) {
                def.checks.forEach((check: any) => {
                  if (check.kind === "min") fieldSchema.minimum = check.value;
                  if (check.kind === "max") fieldSchema.maximum = check.value;
                });
              }
              break;
            case "ZodBoolean":
              fieldSchema.type = "boolean";
              break;
            case "ZodOptional":
              // Recursively handle optional
              const innerSchema = this.zodToOpenAPISchema({ [key]: def.innerType });
              Object.assign(fieldSchema, innerSchema.properties[key]);
              break;
            default:
              fieldSchema.type = "string"; // Fallback
          }

          schema.properties[key] = fieldSchema;

          // Check if required
          if (def.typeName !== "ZodOptional") {
            schema.required.push(key);
          }
        }
      }
    }

    if (schema.required.length === 0) {
      delete schema.required;
    }

    return schema;
  }

  static generateSwaggerHTML(spec: OpenAPISpec): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>${spec.info.title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                spec: ${JSON.stringify(spec, null, 2)},
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            });
        };
    </script>
</body>
</html>`;
  }
}