import express from 'express';
import routes from './routes';
import errorHandler from './middlewares/error.middleware';

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'backend-api' });
});

app.use('/api/v1', routes);

app.use(errorHandler);

export default app;
