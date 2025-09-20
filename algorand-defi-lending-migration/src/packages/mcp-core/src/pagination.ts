/**
 * Pagination utilities for MCP responses
 */
import type { MCPPaginationMetadata } from '@algorand-showcase/types';

/**
 * Pagination helper class
 */
export class PaginationHelper {
  /**
   * Generate a page token
   */
  static generatePageToken(page: number): string {
    return btoa(`page_${page}`);
  }

  /**
   * Decode a page token
   */
  static decodePageToken(token: string): number {
    try {
      const decoded = atob(token);
      const page = parseInt(decoded.replace('page_', ''));
      return isNaN(page) ? 1 : page;
    } catch {
      return 1;
    }
  }

  /**
   * Calculate pagination metadata
   */
  static calculateMetadata(
    totalItems: number,
    itemsPerPage: number,
    currentPage: number
  ): MCPPaginationMetadata {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const hasNextPage = currentPage < totalPages;

    return {
      totalItems,
      itemsPerPage,
      currentPage,
      totalPages,
      hasNextPage,
      ...(hasNextPage && {
        pageToken: this.generatePageToken(currentPage + 1),
      }),
    };
  }

  /**
   * Paginate an array
   */
  static paginateArray<T>(
    array: T[],
    page: number,
    itemsPerPage: number
  ): { items: T[]; metadata: MCPPaginationMetadata } {
    const totalItems = array.length;
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const items = array.slice(startIndex, endIndex);
    const metadata = this.calculateMetadata(totalItems, itemsPerPage, page);

    return { items, metadata };
  }

  /**
   * Extract page number from MCP request parameters
   */
  static extractPageFromParams(params: any): number {
    if (params.pageToken) {
      return this.decodePageToken(params.pageToken);
    }
    if (params.page && typeof params.page === 'number') {
      return Math.max(1, params.page);
    }
    return 1;
  }
}