import { api } from "./api";

export interface Document {
  id: string;
  title: string;
  file_url: string;
  category?: string;
  course_id?: string;
  is_public: boolean;
  uploaded_by: string;
  created_at: string;
}

export interface DocumentListResponse {
  total: number;
  skip: number;
  limit: number;
  data: Document[];
}

export interface KBArticle {
  id: string;
  title: string;
  slug: string;
  content: string;
  summary?: string;
  category?: string;
  status: "DRAFT" | "PUBLISHED" | "ARCHIVED";
  views_count: number;
  likes_count: number;
  created_by: string;
  created_at: string;
  published_at?: string;
}

export interface KBArticleListResponse {
  total: number;
  skip: number;
  limit: number;
  data: KBArticle[];
}

export const documentService = {
  /**
   * List all documents.
   */
  listDocuments: async (skip: number = 0, limit: number = 20, courseId?: string): Promise<DocumentListResponse> => {
    let path = `/documents/?skip=${skip}&limit=${limit}`;
    if (courseId) {
      path += `&course_id=${courseId}`;
    }
    return api.get<DocumentListResponse>(path);
  },

  /**
   * Register document metadata (or upload a file via multipart Form Data).
   */
  registerDocumentMetadata: async (data: {
    title: string;
    file_url: string;
    category?: string;
    course_id?: string;
    is_public?: boolean;
  }): Promise<Document> => {
    return api.post<Document>("/documents/", data);
  },

  /**
   * Upload a raw file (PDF, Word, etc.) to the FastAPI backend.
   */
  uploadDocumentFile: async (file: File, category: string = "Textbook"): Promise<{ file_url: string; title: string }> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);
    return api.postForm<{ file_url: string; title: string }>("/documents/upload", formData);
  },

  /**
   * Get metadata for a specific document.
   */
  getDocument: async (documentId: string): Promise<Document> => {
    return api.get<Document>(`/documents/${documentId}`);
  },

  /**
   * Delete a document. Only the uploader can delete their own documents.
   */
  deleteDocument: async (documentId: string): Promise<void> => {
    return api.del<void>(`/documents/${documentId}`);
  },

  /**
   * Search knowledge base articles using vector search or full-text query.
   */
  searchKnowledgeBase: async (query: string, skip: number = 0, limit: number = 20): Promise<{ query: string; total: number; data: KBArticle[] }> => {
    return api.get<{ query: string; total: number; data: KBArticle[] }>(
      `/knowledge-base/search?q=${encodeURIComponent(query)}&skip=${skip}&limit=${limit}`
    );
  },

  /**
   * Get all knowledge base articles.
   */
  listKBArticles: async (skip: number = 0, limit: number = 20, category?: string): Promise<KBArticleListResponse> => {
    let path = `/knowledge-base/?skip=${skip}&limit=${limit}`;
    if (category) {
      path += `&category=${encodeURIComponent(category)}`;
    }
    return api.get<KBArticleListResponse>(path);
  },

  /**
   * Create a new article.
   */
  createKBArticle: async (articleData: {
    title: string;
    content: string;
    summary?: string;
    category?: string;
    status?: "DRAFT" | "PUBLISHED";
  }): Promise<KBArticle> => {
    return api.post<KBArticle>("/knowledge-base/", articleData);
  },

  /**
   * Like a knowledge base article.
   */
  likeArticle: async (articleId: string): Promise<KBArticle> => {
    return api.post<KBArticle>(`/knowledge-base/${articleId}/like`, {});
  },
};
export type { Document as DocumentType, KBArticle as KBArticleType };
