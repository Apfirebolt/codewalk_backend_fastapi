# Softgenie Portfolio & Blog API 🚀

A robust, high-performance, and scalable backend API built with FastAPI and PostgreSQL to power a personal portfolio platform featuring Blogs, Projects, and Galleries.

This system uses a Unified Content Architecture backed by JSONB fields to support block-based editors (like Editor.js) and flexible metadata without table bloat.

# 🛠️ Technology Stack & Badges

## ✨ Key Features

Unified Content Model: Single table (content_items) handling Blogs, Projects, and Gallery posts differentiated by a content_type enum, eliminating code and table duplication.

Block-Based Editor Support: Fully compatible with Editor.js, storing structured block data natively in PostgreSQL JSONB.

Flexible Metadata: Section-specific fields (e.g., project links, tech stacks) are stored dynamically via extra_metadata JSONB columns.

Cloudinary Integration: Seamless media uploads for user avatars and inline blog/project images.

Robust Authentication: Secure email/password login (with automatic Argon2 hashing and legacy bcrypt fallback) plus Google OAuth2 SSO.

Threadpool-Safe Sync DB Layer: Synchronous SQLAlchemy operations wrapped cleanly in FastAPI's run_in_threadpool for non-blocking asynchronous execution.