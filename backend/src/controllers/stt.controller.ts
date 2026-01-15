import { Request, Response, NextFunction } from 'express';
import { z } from 'zod';

import { SttService } from '../services/stt.service';
import { getOrgContext } from '../utils/requestContext';

const transcribeSchema = z.object({
  language: z.string().optional(),
});

export const transcribe = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const payload = transcribeSchema.parse(req.body ?? {});
    if (!req.file) {
      res.status(400).json({ message: 'audio_file is required' });
      return;
    }

    const context = getOrgContext(req);
    const result = await SttService.transcribe({
      orgId: context.orgId,
      userId: context.userId,
      apiKeyId: context.apiKeyId,
      languageHint: payload.language,
      file: {
        buffer: req.file.buffer,
        mimetype: req.file.mimetype,
        originalname: req.file.originalname,
        size: req.file.size,
      },
    });

    res.json({
      job_id: result.job.id,
      text: result.transcription.text,
      language: result.transcription.language,
      confidence: result.transcription.confidence,
      timestamps: result.transcription.timestamps,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ message: error.message });
      return;
    }
    next(error);
  }
};

export const transcribeRealtimeStub = (_req: Request, res: Response): void => {
  res.status(501).json({ message: 'Realtime transcription will be available in Phase 5' });
};

export const batchTranscribe = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const payload = transcribeSchema.parse(req.body ?? {});
    const files = req.files as Express.Multer.File[];
    if (!files || files.length === 0) {
      res.status(400).json({ message: 'At least one audio_file is required' });
      return;
    }

    const context = getOrgContext(req);

    const jobs = await SttService.batchTranscribe(
      context,
      files.map((file) => ({
        buffer: file.buffer,
        mimetype: file.mimetype,
        originalname: file.originalname,
        size: file.size,
      })),
      payload.language,
    );

    res.json({
      jobs: jobs.map((job) => ({ id: job.id, status: job.status, language: job.languageDetected })),
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      res.status(400).json({ message: error.message });
      return;
    }
    next(error);
  }
};
