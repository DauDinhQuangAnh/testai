// Phai khop backend/schemas.py.

export interface UserOut {
  id: string;
  email: string;
  created_at?: string | null;
}

export interface TokenOut {
  token: string;
  role: "user" | "admin";
  user: UserOut;
}

export interface JobOut {
  id: string;
  user_id: string | null;
  filename: string;
  status: "queued" | "running" | "done" | "failed";
  stage: string | null;
  stage_label: string;
  progress: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface FileOut {
  name: string;
  format: string;
  size_bytes: number;
}

export interface SubtitleGroupOut {
  language: string;
  label: string;
  files: FileOut[];
  preview_text: string | null;
}

export interface VideoOut {
  name: string;
  language: string;
  size_bytes: number;
}

export interface JobFilesOut {
  videos: VideoOut[];
  subtitles: SubtitleGroupOut[];
}

export interface VoiceInfo {
  label: string;
  id: string;
  gender: string;
  style: string;
  recommended: boolean;
}

export interface AdminUserOut {
  id: string;
  email: string;
  created_at: string;
  job_count: number;
}

// Schema options giu NGUYEN dict cua wizard cu (job_config.json) - worker
// khong doi gi.
export interface JobOptions {
  source: {
    url: string | null;
    quality: "720p" | "best";
    trim_seconds: number | null;
    source_language: string | null;
  };
  dubbing: {
    enabled: boolean;
    target_language: string;
    voice: string | null;
    rate_percent: number;
    pitch_hz: number;
  };
  translation: {
    glossary: string;
    max_chars_per_line: number;
    max_lines: number;
  };
  subtitle: {
    burn_in: boolean;
    style: {
      font: string;
      font_size: number;
      text_color: string;
      outline_color: string;
      outline_width: number;
      position: "bottom" | "middle" | "top";
      opaque_box: boolean;
    };
  };
  audio: {
    original_volume: number;
    dub_volume: number;
    ducking: boolean;
  };
  output: {
    format: "mp4" | "mkv";
    quality: "fast" | "balanced" | "high";
  };
}

export function defaultOptions(): JobOptions {
  return {
    source: { url: null, quality: "720p", trim_seconds: null, source_language: null },
    dubbing: {
      enabled: true,
      target_language: "vi",
      voice: null,
      rate_percent: 0,
      pitch_hz: 0,
    },
    translation: { glossary: "", max_chars_per_line: 42, max_lines: 2 },
    subtitle: {
      burn_in: false,
      style: {
        font: "Arial",
        font_size: 48,
        text_color: "#FFFFFF",
        outline_color: "#000000",
        outline_width: 2,
        position: "bottom",
        opaque_box: false,
      },
    },
    audio: { original_volume: 0, dub_volume: 1, ducking: false },
    output: { format: "mp4", quality: "balanced" },
  };
}
