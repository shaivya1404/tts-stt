import { AudioFileType, JobStatus } from '@prisma/client';

import prisma from '../lib/prisma';
import { mlSttClient } from './mlSttClient';
import storageService from '../utils/storage';

interface TranscribeInput {
  orgId: string;
  userId?: string;
  apiKeyId?: string;
  languageHint?: string;
  file: { buffer: Buffer; mimetype: string; originalname: string; size: number };
}

export const SttService = {
  async transcribe(input: TranscribeInput) {
    const storageKey = await storageService.uploadBuffer(input.file.buffer, input.file.mimetype, {
      prefix: 'stt-input',
      extension: input.file.originalname.split('.').pop(),
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
        modelUsed: 'conformer_rnnt',
        status: JobStatus.processing,
      },
    });

    try {
      const mlResponse = await mlSttClient.transcribe({
        buffer: input.file.buffer,
        filename: input.file.originalname,
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

      const durationSeconds = mlResponse.timestamps?.length
        ? mlResponse.timestamps[mlResponse.timestamps.length - 1].end
        : undefined;

      if (durationSeconds) {
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
          completedAt: new Date(),
        },
      });

      await prisma.usageRecord.create({
        data: {
          orgId: input.orgId,
          apiKeyId: input.apiKeyId,
          type: 'stt',
          units: durationSeconds || 0,
          metadata: {
            jobId: job.id,
            inputAudioFileId: audioFile.id,
          },
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
    files: Array<{ buffer: Buffer; mimetype: string; originalname: string; size: number }>,
    languageHint?: string,
  ) {
    const jobs = [];
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
      jobs.push(result.job);
    }
    return jobs;
  },
};
