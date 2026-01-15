import { AudioFileType, JobStatus, SttJob, Transcription, UsageType } from '@prisma/client';

import prisma from '../lib/prisma';
import { mlSttClient, MlSttTranscribeResult } from './mlSttClient.service';
import storageService from '../utils/storage';
import { UsageService } from './usage.service';

interface UploadedFile {
  buffer: Buffer;
  mimetype: string;
  originalname: string;
  size: number;
}

interface TranscribeInput {
  orgId: string;
  userId?: string;
  apiKeyId?: string;
  languageHint?: string;
  file: UploadedFile;
}

interface TranscribeResult {
  job: SttJob;
  transcription: Transcription;
}

const extractExtension = (fileName: string): string | undefined => {
  const parts = fileName.split('.');
  if (parts.length < 2) {
    return undefined;
  }
  return parts.pop();
};

const getNumericMeta = (meta: Record<string, unknown> | undefined, key: string): number | undefined => {
  if (!meta) {
    return undefined;
  }
  const value = meta[key];
  return typeof value === 'number' ? value : undefined;
};

const resolveDurationSeconds = (mlResponse: MlSttTranscribeResult): number | undefined => {
  const metaDuration =
    getNumericMeta(mlResponse.meta, 'duration_seconds') ?? getNumericMeta(mlResponse.meta, 'durationSeconds');
  if (typeof metaDuration === 'number') {
    return metaDuration;
  }

  const lastTimestamp = mlResponse.timestamps?.[mlResponse.timestamps.length - 1];
  if (lastTimestamp && typeof lastTimestamp.end === 'number') {
    return lastTimestamp.end;
  }

  return undefined;
};

export const SttService = {
  async transcribe(input: TranscribeInput): Promise<TranscribeResult> {
    const storageKey = await storageService.uploadBuffer(input.file.buffer, input.file.mimetype, {
      prefix: `stt-input/${input.orgId}`,
      extension: extractExtension(input.file.originalname),
    });

    const audioFile = await prisma.audioFile.create({
      data: {
        orgId: input.orgId,
        userId: input.userId,
        type: AudioFileType.stt_input,
        storagePath: storageKey,
        mimeType: input.file.mimetype,
        sizeBytes: input.file.size,
      },
    });

    const job = await prisma.sttJob.create({
      data: {
        orgId: input.orgId,
        userId: input.userId,
        apiKeyId: input.apiKeyId,
        inputAudioFileId: audioFile.id,
        modelUsed: 'stt_pipeline_pending',
        status: JobStatus.processing,
      },
    });

    try {
      const mlResponse = await mlSttClient.transcribeWithMl({
        buffer: input.file.buffer,
        fileName: input.file.originalname,
        mimeType: input.file.mimetype,
        languageHint: input.languageHint,
      });

      const transcription = await prisma.transcription.create({
        data: {
          sttJobId: job.id,
          text: mlResponse.text,
          language: mlResponse.language,
          confidence: mlResponse.confidence,
          timestamps: mlResponse.timestamps,
        },
      });

      const durationSeconds = resolveDurationSeconds(mlResponse);

      if (typeof durationSeconds === 'number') {
        await prisma.audioFile.update({
          where: { id: audioFile.id },
          data: { durationSeconds },
        });
      }

      const updatedJob = await prisma.sttJob.update({
        where: { id: job.id },
        data: {
          status: JobStatus.completed,
          languageDetected: mlResponse.language,
          modelUsed: mlResponse.modelUsed || job.modelUsed,
          completedAt: new Date(),
        },
      });

      await UsageService.recordUsage({
        orgId: input.orgId,
        apiKeyId: input.apiKeyId,
        type: UsageType.stt,
        units: durationSeconds ?? 0,
        metadata: {
          jobId: job.id,
          inputAudioFileId: audioFile.id,
          modelUsed: mlResponse.modelUsed,
          durationSeconds: durationSeconds ?? 0,
        },
      });

      return { job: updatedJob, transcription };
    } catch (error) {
      await prisma.sttJob.update({
        where: { id: job.id },
        data: {
          status: JobStatus.failed,
          errorMessage: error instanceof Error ? error.message : 'STT transcription failed',
        },
      });
      throw error;
    }
  },

  async batchTranscribe(
    context: { orgId: string; userId?: string; apiKeyId?: string },
    files: UploadedFile[],
    languageHint?: string,
  ): Promise<TranscribeResult[]> {
    const jobs: TranscribeResult[] = [];
    // eslint-disable-next-line no-restricted-syntax
    for (const file of files) {
      // eslint-disable-next-line no-await-in-loop
      const result = await SttService.transcribe({
        orgId: context.orgId,
        userId: context.userId,
        apiKeyId: context.apiKeyId,
        languageHint,
        file,
      });
      jobs.push(result);
    }
    return jobs;
  },
};
