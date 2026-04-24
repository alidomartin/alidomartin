import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import PostList from './components/PostList';
import ContentWheel from './components/ContentWheel';
import CreatePostModal from './components/CreatePostModal';
import { usePosts } from './hooks/usePosts';

export default function App() {
  const { posts, addPost, updatePost, deletePost, markPosted } = usePosts();
  const [view, setView] = useState('dashboard');
  const [showModal, setShowModal] = useState(false);
  const [editingPost, setEditingPost] = useState(null);

  function openCreate() {
    setEditingPost(null);
    setShowModal(true);
  }

  function openEdit(post) {
    setEditingPost(post);
    setShowModal(true);
  }

  function handleSave(data) {
    if (editingPost) {
      updatePost(editingPost.id, data);
    } else {
      addPost(data);
    }
  }

  function handleDelete(id) {
    if (window.confirm('Delete this post?')) deletePost(id);
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar
        activeView={view}
        onViewChange={setView}
        onNewPost={openCreate}
      />

      <main className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-6 space-y-6">
          {view === 'dashboard' && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                <div className="lg:col-span-3">
                  <Dashboard
                    posts={posts}
                    onNewPost={openCreate}
                  />
                </div>
                <div className="lg:col-span-2">
                  <ContentWheel posts={posts} />
                </div>
              </div>
            </>
          )}

          {view === 'schedule' && (
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3">
                <PostList
                  posts={posts}
                  onEdit={openEdit}
                  onDelete={handleDelete}
                  onMarkPosted={markPosted}
                />
              </div>
              <div className="lg:col-span-2">
                <ContentWheel posts={posts} />
              </div>
            </div>
          )}
        </div>
      </main>

      {showModal && (
        <CreatePostModal
          posts={posts}
          editingPost={editingPost}
          onSave={handleSave}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}
