import { Router } from 'express';
import { UserRole } from '@prisma/client';

import { getModelsStatus, reloadModels } from '../controllers/models.controller';
import { requireJwt, requireRole } from '../middlewares/auth.middleware';

const router = Router();

router.get('/status', requireJwt, getModelsStatus);
router.post('/reload', requireJwt, requireRole([UserRole.owner, UserRole.admin]), reloadModels);

export default router;
