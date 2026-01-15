import { AudioFileType, JobStatus } from '@prisma/client';

import prisma from '../lib/prisma';
import { mlTtsClient } from './mlTtsClient';
import storageService from '../utils/storage';

interface SynthesizeInput {
  orgId: string;
  userId?: string;
  apiKeyId?: string;
  text: string;
  language: string;
  voiceId?: string;
  emotion?: string;
  speed?: number;
}

export const TtsService = {
  async synthesize(input: SynthesizeInput) {
    const job = await prisma.ttsJob.create({
      data: {
        orgId: input.orgId,
        userId: input.userId,
        apiKeyId: input.apiKeyId,
        inputText: input.text,
        language: input.language,
        voiceProfileId: input.voiceId,
        emotion: input.emotion,
        speed: input.speed,
        status: JobStatus.processing,
      },
    });

    try {
      const mlResponse = await mlTtsClient.synthesize({
        text: input.text,
        language: input.language,
        voiceId: input.voiceId,
        emotion: input.emotion,
        speed: input.speed,
      });

      const audioFile = await prisma.audioFile.create({
        data: {
          orgId: input.orgId,
          userId: input.userId,
          type: AudioFileType.tts_output,
          storagePath: mlResponse.audioUrl,
          mimeType: 'audio/wav',
          durationSeconds: mlResponse.duration,
        },
      });

      const updatedJob = await prisma.ttsJob.update({
        where: { id: job.id },
        data: {
          status: JobStatus.completed,
          resultAudioFileId: audioFile.id,
          completedAt: new Date(),
        },
      });

      await prisma.usageRecord.create({
        data: {
          orgId: input.orgId,
          apiKeyId: input.apiKeyId,
          type: 'tts',
          units: input.text.length,
          metadata: {
            jobId: job.id,
            voiceProfileId: input.voiceId,
          },
        },
      });

      return { job: updatedJob, audioFile, mlResponse };
    } catch (error) {
      await prisma.ttsJob.update({
        where: { id: job.id },
        data: {
          status: JobStatus.failed,
          errorMessage: error instanceof Error ? error.message : 'TTS synthesis failed',
        },
      });
      throw error;
    }
  },

  async synthesizeBatch(
    orgContext: { orgId: string; userId?: string; apiKeyId?: string },
    requests: Array<Omit<SynthesizeInput, 'orgId' | 'userId' | 'apiKeyId'>>,
  ) {
    const results: Array<{ jobId: string; status: JobStatus; audioUrl?: string; duration?: number }> = [];
    // eslint-disable-next-line no-restricted-syntax
    for (const item of requests) {
      // eslint-disable-next-line no-await-in-loop
      const { job, mlResponse } = await TtsService.synthesize({
        ...item,
        orgId: orgContext.orgId,
        userId: orgContext.userId,
        apiKeyId: orgContext.apiKeyId,
      });
      results.push({
        jobId: job.id,
        status: job.status,
        audioUrl: mlResponse.audioUrl,
        duration: mlResponse.duration,
      });
    }
    return results;
  },

  async listVoices(orgId: string) {
    return prisma.voiceProfile.findMany({
      where: { orgId },
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        name: true,
        language: true,
        gender: true,
        description: true,
        status: true,
      },
    });
  },

  async cloneVoice(input: {
    orgId: string;
    userId?: string;
    file: { buffer: Buffer; mimetype: string; size: number; originalname: string };
    name: string;
    language: string;
    gender?: string;
    description?: string;
    baseModel?: string;
  }) {
    const storageKey = await storageService.uploadBuffer(input.file.buffer, input.file.mimetype, {
      prefix: 'voice-clone-samples',
      extension: input.file.originalname.split('.').pop(),
    });

    await prisma.audioFile.create({
      data: {
        orgId: input.orgId,
        userId: input.userId,
        type: AudioFileType.voice_clone_sample,
        storagePath: storageKey,
        mimeType: input.file.mimetype,
        sizeBytes: input.file.size,
      },
    });

    return prisma.voiceProfile.create({
      data: {
        orgId: input.orgId,
        name: input.name,
        language: input.language,
        gender: input.gender,
        description: input.description,
        baseModel: input.baseModel || 'vits_indic_v1',
        speakerEmbeddingPath: storageKey,
        status: 'training',
      },
    });
  },
};
