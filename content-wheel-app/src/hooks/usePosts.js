import { useState, useEffect } from 'react';

const STORAGE_KEY = 'content-wheel-posts';

function loadPosts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function savePosts(posts) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(posts));
}

function generateId() {
  return `post_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export function usePosts() {
  const [posts, setPosts] = useState(loadPosts);

  useEffect(() => {
    savePosts(posts);
  }, [posts]);

  function addPost(data) {
    const post = {
      id: generateId(),
      createdAt: new Date().toISOString(),
      ...data,
    };
    setPosts(prev => [...prev, post]);
    return post;
  }

  function updatePost(id, data) {
    setPosts(prev => prev.map(p => p.id === id ? { ...p, ...data } : p));
  }

  function deletePost(id) {
    setPosts(prev => prev.filter(p => p.id !== id));
  }

  function markPosted(id) {
    setPosts(prev => prev.map(p => p.id === id ? { ...p, status: 'posted', postedAt: new Date().toISOString() } : p));
  }

  return { posts, addPost, updatePost, deletePost, markPosted };
}
