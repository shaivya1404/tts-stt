import axios from 'axios';
import FormData from 'form-data';

import config from '../config';

export interface SttTranscribeInput {
  buffer: Buffer;
  filename: string;
  mimeType: string;
  languageHint?: string;
}

export interface SttTranscribeResult {
  text: string;
  language: string;
  confidence: number;
  timestamps: Array<{ start: number; end: number; word: string }>;
}

const BASE_URL = config.services.sttServiceUrl;

export const mlSttClient = {
  async transcribe(input: SttTranscribeInput): Promise<SttTranscribeResult> {
    const formData = new FormData();
    formData.append('file', input.buffer, {
      filename: input.filename,
      contentType: input.mimeType,
    });

    if (input.languageHint) {
      formData.append('language', input.languageHint);
    }

    const response = await axios.post(`${BASE_URL}/ml/stt/transcribe`, formData, {
      headers: formData.getHeaders(),
      maxBodyLength: Infinity,
    });

    return {
      text: response.data.text,
      language: response.data.language,
      confidence: response.data.confidence,
      timestamps: response.data.timestamps || [],
    };
  },

  async health(): Promise<{ status: string }> {
    const response = await axios.get(`${BASE_URL}/ml/stt/health`);
    return response.data;
  },

  async initialize(): Promise<{ status: string; detail?: string }> {
    const response = await axios.post(`${BASE_URL}/ml/stt/initialize`);
    return response.data;
  },
};
