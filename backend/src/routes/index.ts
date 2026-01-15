import { Router } from 'express';

const router = Router();

router.get('/', (_req, res) => {
  res.json({ message: 'TTS/STT API v1', status: 'running' });
});

export default router;
