import axios from 'axios';

import config from '../config';

export interface TtsSynthesizeInput {
  text: string;
  language: string;
  voiceId?: string;
  emotion?: string;
  speed?: number;
}

export interface TtsSynthesizeResult {
  audioUrl: string;
  duration: number;
  status: string;
}

const BASE_URL = config.services.ttsServiceUrl;

export const mlTtsClient = {
  async synthesize(payload: TtsSynthesizeInput): Promise<TtsSynthesizeResult> {
    const response = await axios.post(`${BASE_URL}/ml/tts/predict`, {
      text: payload.text,
      language: payload.language,
      voice_id: payload.voiceId,
      emotion: payload.emotion,
      speed: payload.speed,
    });

    return {
      audioUrl: response.data.audio_url,
      duration: response.data.duration,
      status: response.data.status,
    };
  },

  async health(): Promise<{ status: string }> {
    const response = await axios.get(`${BASE_URL}/ml/tts/health`);
    return response.data;
  },

  async initialize(): Promise<{ status: string; detail?: string }> {
    const response = await axios.post(`${BASE_URL}/ml/tts/initialize`);
    return response.data;
  },
};
