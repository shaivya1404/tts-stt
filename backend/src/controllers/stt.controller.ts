import { Request, Response, NextFunction } from 'express';

import { SttService } from '../services/stt.service';
import { getOrgContext } from '../utils/requestContext';

const extractLanguageHint = (value: unknown): string | undefined => {
  if (typeof value !== 'string') {
    return undefined;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
};

const mapUploadedFile = (file: Express.Multer.File) => ({
  buffer: file.buffer,
  mimetype: file.mimetype,
  originalname: file.originalname,
  size: file.size,
});

export const transcribe = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    if (!req.file) {
      res.status(400).json({ message: 'audio_file is required' });
      return;
    }

    const context = getOrgContext(req);
    const languageHint = extractLanguageHint(req.query.language_hint);

    const result = await SttService.transcribe({
      orgId: context.orgId,
      userId: context.userId,
      apiKeyId: context.apiKeyId,
      languageHint,
      file: mapUploadedFile(req.file),
    });

    res.json({
      job_id: result.job.id,
      text: result.transcription.text,
      language: result.transcription.language,
      confidence: result.transcription.confidence,
      timestamps: result.transcription.timestamps,
    });
  } catch (error) {
    next(error);
  }
};

export const transcribeRealtimeStub = (_req: Request, res: Response): void => {
  res.status(501).json({ message: 'Realtime transcription will be available in Phase 5' });
};

export const batchTranscribe = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const files = (req.files as Express.Multer.File[] | undefined) ?? [];
    if (!files.length) {
      res.status(400).json({ message: 'At least one audio_file is required' });
      return;
    }

    const context = getOrgContext(req);
    const languageHint = extractLanguageHint(req.query.language_hint);

    const jobs = await SttService.batchTranscribe(
      context,
      files.map((file) => mapUploadedFile(file)),
      languageHint,
    );

    res.json({
      items: jobs.map((result) => ({
        job_id: result.job.id,
        text: result.transcription.text,
        language: result.transcription.language,
        confidence: result.transcription.confidence,
        timestamps: result.transcription.timestamps,
      })),
    });
  } catch (error) {
    next(error);
  }
};
