import { useState } from "react";
import { Camera as CameraIcon, Plus, Pencil, Trash2, X, Video, VideoOff } from "lucide-react";

import { useAppContent } from "../context/AppContent";
import LiveStream from "../components/LiveStream";

const EMPTY_FORM = { name: "", location: "", feed_url: "", is_active: true };

function CameraForm({ initial, onCancel, onSubmit }) {
  const [form, setForm] = useState(initial || EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(form);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="card p-4 space-y-3 border border-primary/20"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">
          {initial ? "Edit camera" : "Add camera"}
        </h3>
        <button type="button" onClick={onCancel} className="text-gray-400 hover:text-gray-600">
          <X size={16} />
        </button>
      </div>

      <div>
        <label className="text-xs font-medium text-gray-600">Name</label>
        <input
          name="name"
          required
          value={form.name}
          onChange={handleChange}
          placeholder="Gate 2 — Crane Zone"
          className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40"
        />
      </div>

      <div>
        <label className="text-xs font-medium text-gray-600">Location</label>
        <input
          name="location"
          value={form.location}
          onChange={handleChange}
          placeholder="North yard"
          className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40"
        />
      </div>

      <div>
        <label className="text-xs font-medium text-gray-600">Feed URL</label>
        <input
          name="feed_url"
          value={form.feed_url}
          onChange={handleChange}
          placeholder="rtsp://…"
          className="mt-1 w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/40"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input
          type="checkbox"
          name="is_active"
          checked={!!form.is_active}
          onChange={handleChange}
        />
        Active
      </label>

      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={submitting}
          className="flex-1 bg-primary text-white text-sm font-medium py-2 rounded-lg hover:opacity-90 transition disabled:opacity-50"
        >
          {submitting ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 border border-gray-200 text-sm font-medium py-2 rounded-lg hover:bg-gray-50 transition"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export default function Camera() {
  const { cameras } = useAppContent();
  const { cameras: list, loading, error, addCamera, editCamera, removeCamera } = cameras;

  const [mode, setMode] = useState(null); // null | "add" | camera.id being edited
  const [liveIds, setLiveIds] = useState(() => new Set());

  const toggleLive = (id) => {
    setLiveIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleAdd = async (form) => {
    await addCamera(form);
    setMode(null);
  };

  const handleEdit = async (id, form) => {
    await editCamera(id, form);
    setMode(null);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Remove this camera?")) return;
    await removeCamera(id);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Cameras</h1>
          <p className="text-sm text-gray-500">
            Manage the camera feeds monitored by the detection pipeline
          </p>
        </div>
        <button
          onClick={() => setMode("add")}
          className="flex items-center gap-1.5 bg-primary text-white text-sm font-medium px-3 py-2 rounded-lg hover:opacity-90 transition"
        >
          <Plus size={16} />
          Add camera
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-danger/10 text-danger text-sm px-3 py-2">
          {error}
        </div>
      )}

      {mode === "add" && (
        <CameraForm onCancel={() => setMode(null)} onSubmit={handleAdd} />
      )}

      {loading ? (
        <p className="text-sm text-gray-500">Loading cameras…</p>
      ) : list.length === 0 && mode !== "add" ? (
        <div className="card flex flex-col items-center text-center py-10 gap-2">
          <CameraIcon className="text-gray-300" size={28} />
          <p className="text-sm text-gray-500">No cameras added yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {list.map((cam) =>
            mode === cam.id ? (
              <CameraForm
                key={cam.id}
                initial={cam}
                onCancel={() => setMode(null)}
                onSubmit={(form) => handleEdit(cam.id, form)}
              />
            ) : (
              <div key={cam.id} className="card p-4 space-y-3">
                {liveIds.has(cam.id) ? (
                  <LiveStream cameraId={cam.id} cameraName={cam.name} enabled />
                ) : (
                  <div className="flex items-start justify-between">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <CameraIcon className="text-primary" size={18} />
                    </div>
                    <span
                      className={`text-xs font-medium px-2 py-1 rounded-full ${
                        cam.is_active !== false
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {cam.is_active !== false ? "Active" : "Inactive"}
                    </span>
                  </div>
                )}

                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {cam.name || `Camera #${cam.id}`}
                  </p>
                  <p className="text-xs text-gray-500">
                    {cam.location || "No location set"}
                  </p>
                </div>

                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => toggleLive(cam.id)}
                    disabled={cam.is_active === false}
                    className="flex items-center gap-1 text-xs font-medium text-primary border border-primary/20 rounded-lg px-2.5 py-1.5 hover:bg-primary/10 transition disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {liveIds.has(cam.id) ? <VideoOff size={13} /> : <Video size={13} />}
                    {liveIds.has(cam.id) ? "Stop" : "View live"}
                  </button>
                  <button
                    onClick={() => setMode(cam.id)}
                    className="flex items-center gap-1 text-xs font-medium text-gray-600 border border-gray-200 rounded-lg px-2.5 py-1.5 hover:bg-gray-50 transition"
                  >
                    <Pencil size={13} />
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(cam.id)}
                    className="flex items-center gap-1 text-xs font-medium text-danger border border-danger/20 rounded-lg px-2.5 py-1.5 hover:bg-danger/10 transition"
                  >
                    <Trash2 size={13} />
                    Remove
                  </button>
                </div>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}
