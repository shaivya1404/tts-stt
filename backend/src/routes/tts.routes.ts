import { Router } from 'express';
import multer from 'multer';
import { UserRole } from '@prisma/client';

import { synthesize, synthesizeBatch, listVoices, voiceClone } from '../controllers/tts.controller';
import { optionalJwt, requireAuthOrApiKey, requireRole } from '../middlewares/auth.middleware';
import { optionalApiKey, requireOrgContext, ensureScopeWhenPresent } from '../middlewares/apiKey.middleware';
import { rateLimit } from '../middlewares/rateLimit.middleware';

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });

const router = Router();

router.post(
  '/synthesize',
  optionalJwt,
  optionalApiKey,
  ensureScopeWhenPresent('tts'),
  requireAuthOrApiKey,
  requireOrgContext,
  rateLimit(),
  synthesize,
);
router.post(
  '/synthesize-batch',
  optionalJwt,
  optionalApiKey,
  ensureScopeWhenPresent('tts'),
  requireAuthOrApiKey,
  requireOrgContext,
  rateLimit(),
  synthesizeBatch,
);
router.get(
  '/voices',
  optionalJwt,
  optionalApiKey,
  ensureScopeWhenPresent('tts'),
  requireAuthOrApiKey,
  requireOrgContext,
  listVoices,
);
router.post(
  '/voice-clone',
  optionalJwt,
  optionalApiKey,
  ensureScopeWhenPresent('tts'),
  requireAuthOrApiKey,
  requireOrgContext,
  requireRole([UserRole.owner, UserRole.admin, UserRole.developer]),
  upload.single('audio_sample'),
  voiceClone,
);

export default router;
