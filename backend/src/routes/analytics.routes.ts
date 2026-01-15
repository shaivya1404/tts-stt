import { Router } from 'express';

import { getUsage } from '../controllers/analytics.controller';
import { requireJwt } from '../middlewares/auth.middleware';

const router = Router();

router.get('/usage', requireJwt, getUsage);

export default router;
