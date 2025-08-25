/**
 * Mock Database Service
 *
 * Provides a mock implementation of the DatabaseService interface
 * for development and testing purposes.
 */

import { DatabaseService, ContentQuery } from "../types/module";

export class MockDatabaseService implements DatabaseService {
  private storage: Map<string, any> = new Map();
  private sessions: Map<string, any> = new Map();
  private content: Map<string, any> = new Map();

  constructor() {
    // Initialize with some mock data
    this.initializeMockData();
  }

  // User data operations
  async getUserData(userId: string, dataType: string): Promise<any> {
    const key = `${userId}:${dataType}`;
    const data = this.storage.get(key);

    console.log(`MockDB: Getting user data for ${key}:`, data);
    return data || null;
  }

  async saveUserData(
    userId: string,
    dataType: string,
    data: any
  ): Promise<void> {
    const key = `${userId}:${dataType}`;
    this.storage.set(key, { ...data, lastUpdated: new Date().toISOString() });

    console.log(`MockDB: Saved user data for ${key}:`, data);
  }

  async deleteUserData(userId: string, dataType: string): Promise<void> {
    const key = `${userId}:${dataType}`;
    this.storage.delete(key);

    console.log(`MockDB: Deleted user data for ${key}`);
  }

  // Content operations
  async getContent(contentId: string): Promise<any> {
    const content = this.content.get(contentId);

    console.log(`MockDB: Getting content ${contentId}:`, content);
    return content || null;
  }

  async saveContent(content: any): Promise<string> {
    const contentId =
      content.id ||
      `content_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const contentWithMetadata = {
      ...content,
      id: contentId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.content.set(contentId, contentWithMetadata);

    console.log(`MockDB: Saved content ${contentId}:`, contentWithMetadata);
    return contentId;
  }

  async searchContent(query: ContentQuery): Promise<any[]> {
    const allContent = Array.from(this.content.values());
    let results = allContent;

    // Apply filters
    if (query.type) {
      results = results.filter((content) => content.type === query.type);
    }

    if (query.difficulty) {
      results = results.filter(
        (content) => content.difficulty === query.difficulty
      );
    }

    if (query.tags && query.tags.length > 0) {
      results = results.filter(
        (content) =>
          content.tags && query.tags!.some((tag) => content.tags.includes(tag))
      );
    }

    // Apply pagination
    const offset = query.offset || 0;
    const limit = query.limit || 50;
    results = results.slice(offset, offset + limit);

    console.log(
      `MockDB: Search content with query:`,
      query,
      `Found ${results.length} results`
    );
    return results;
  }

  // Progress tracking
  async getProgress(userId: string, moduleId: string): Promise<any> {
    const key = `${userId}:progress:${moduleId}`;
    const progress = this.storage.get(key);

    console.log(`MockDB: Getting progress for ${key}:`, progress);
    return progress || null;
  }

  async updateProgress(
    userId: string,
    moduleId: string,
    progress: any
  ): Promise<void> {
    const key = `${userId}:progress:${moduleId}`;
    const progressWithMetadata = {
      ...progress,
      userId,
      moduleId,
      lastUpdated: new Date().toISOString(),
    };

    this.storage.set(key, progressWithMetadata);

    console.log(`MockDB: Updated progress for ${key}:`, progressWithMetadata);
  }

  // Session management
  async createSession(sessionData: any): Promise<string> {
    const sessionId =
      sessionData.id ||
      `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const sessionWithMetadata = {
      ...sessionData,
      id: sessionId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    this.sessions.set(sessionId, sessionWithMetadata);

    console.log(`MockDB: Created session ${sessionId}:`, sessionWithMetadata);
    return sessionId;
  }

  async updateSession(sessionId: string, sessionData: any): Promise<void> {
    const existingSession = this.sessions.get(sessionId);
    if (!existingSession) {
      throw new Error(`Session ${sessionId} not found`);
    }

    const updatedSession = {
      ...existingSession,
      ...sessionData,
      updatedAt: new Date().toISOString(),
    };

    this.sessions.set(sessionId, updatedSession);

    console.log(`MockDB: Updated session ${sessionId}:`, updatedSession);
  }

  async getSession(sessionId: string): Promise<any> {
    const session = this.sessions.get(sessionId);

    console.log(`MockDB: Getting session ${sessionId}:`, session);
    return session || null;
  }

  // Helper methods for testing and development
  public getAllData(): Map<string, any> {
    return new Map(this.storage);
  }

  public getAllSessions(): Map<string, any> {
    return new Map(this.sessions);
  }

  public getAllContent(): Map<string, any> {
    return new Map(this.content);
  }

  public clearAllData(): void {
    this.storage.clear();
    this.sessions.clear();
    this.content.clear();
    console.log("MockDB: All data cleared");
  }

  private initializeMockData(): void {
    // Add some sample stories
    const sampleStories = [
      {
        id: "story_1",
        title: "The Friendly Cat",
        type: "story",
        difficulty: "amateur",
        sentences: [
          "The cat is happy.",
          "The cat likes to play.",
          "The cat runs fast.",
        ],
        tags: ["animals", "beginner", "simple"],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      {
        id: "story_2",
        title: "A Day at School",
        type: "story",
        difficulty: "normal",
        sentences: [
          "I go to school every day.",
          "My teacher is very kind.",
          "I learn many new things.",
          "School is fun and exciting.",
        ],
        tags: ["education", "daily-life", "intermediate"],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
      {
        id: "story_3",
        title: "The Magic Garden",
        type: "story",
        difficulty: "mid_level",
        sentences: [
          "In the garden, flowers bloom beautifully.",
          "The gardener waters the plants carefully.",
          "Butterflies dance among the colorful flowers.",
          "The garden is a peaceful place to visit.",
          "Many people come to enjoy the natural beauty.",
        ],
        tags: ["nature", "descriptive", "intermediate"],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    sampleStories.forEach((story) => {
      this.content.set(story.id, story);
    });

    console.log("MockDB: Initialized with sample data");
  }
}

export default MockDatabaseService;
