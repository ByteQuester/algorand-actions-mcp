/**
 * Example script showing how to use ResponseProcessor with debug logging
 */
import { ResponseProcessor } from '../../src/response-processor.js';

// Simple logger for testing
const testLogger = {
  debug: (message: string, data?: any) => {
    console.log(`[DEBUG] ${message}`, data ? JSON.stringify(data, null, 2) : '');
  },
  info: (message: string, data?: any) => {
    console.log(`[INFO] ${message}`, data ? JSON.stringify(data, null, 2) : '');
  }
};

// Example usage with debug logging
export function testResponseProcessor() {
  console.log('=== Testing ResponseProcessor with Debug Logging ===\n');

  // Enable debug logging
  ResponseProcessor.setLogger(testLogger);
  ResponseProcessor.setItemsPerPage(3); // Small page size for testing

  // Test array response
  console.log('1. Testing array response with pagination:');
  const largeArray = Array.from({ length: 10 }, (_, i) => ({ id: i, name: `Item ${i}` }));
  const arrayResult = ResponseProcessor.processResponse(largeArray);
  console.log('Result:', JSON.parse(arrayResult.content[0].text));

  console.log('\n2. Testing small array response (no pagination):');
  const smallArray = [{ id: 1, name: 'Item 1' }, { id: 2, name: 'Item 2' }];
  const smallArrayResult = ResponseProcessor.processResponse(smallArray);
  console.log('Result:', JSON.parse(smallArrayResult.content[0].text));

  console.log('\n3. Testing object response with array field:');
  const objectWithArray = {
    metadata: { total: 10 },
    items: Array.from({ length: 8 }, (_, i) => ({ id: i, name: `Object Item ${i}` }))
  };
  const objectResult = ResponseProcessor.processResponse(objectWithArray);
  console.log('Result:', JSON.parse(objectResult.content[0].text));

  console.log('\n4. Testing simple value response:');
  const simpleValue = { message: 'Hello World', status: 'success' };
  const simpleResult = ResponseProcessor.processResponse(simpleValue);
  console.log('Result:', JSON.parse(simpleResult.content[0].text));

  // Reset to production mode
  console.log('\n5. Testing production mode (no debug logs):');
  ResponseProcessor.resetLogger();
  const prodResult = ResponseProcessor.processResponse(largeArray);
  console.log('Production result (no debug logs shown above)');

  console.log('\n=== Test Complete ===');
}

// Run test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testResponseProcessor();
}