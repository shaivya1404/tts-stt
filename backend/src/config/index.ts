import dotenv from 'dotenv';

dotenv.config();

interface ServiceConfig {
  ttsServiceUrl: string;
  sttServiceUrl: string;
}

interface PostgresConfig {
  host: string;
  port: number;
  user: string;
  password: string;
  database: string;
}

interface RedisConfig {
  host: string;
  port: number;
  password?: string;
}

export interface AppConfig {
  env: string;
  port: number;
  postgres: PostgresConfig;
  redis: RedisConfig;
  services: ServiceConfig;
}

const toNumber = (value: string | undefined, fallback: number): number => {
  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    return fallback;
  }
  return parsed;
};

const config: AppConfig = {
  env: process.env.NODE_ENV || 'development',
  port: toNumber(process.env.BACKEND_PORT, 4000),
  postgres: {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: toNumber(process.env.POSTGRES_PORT, 5432),
    user: process.env.POSTGRES_USER || 'postgres',
    password: process.env.POSTGRES_PASSWORD || 'postgres',
    database: process.env.POSTGRES_DB || 'tts_stt',
  },
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: toNumber(process.env.REDIS_PORT, 6379),
    password: process.env.REDIS_PASSWORD,
  },
  services: {
    ttsServiceUrl: process.env.TTS_SERVICE_URL || 'http://localhost:8001',
    sttServiceUrl: process.env.STT_SERVICE_URL || 'http://localhost:8002',
  },
};

export default config;
