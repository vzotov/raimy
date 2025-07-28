// lib/livekit.ts
import { AccessToken } from 'livekit-server-sdk';

const apiKey = process.env.LIVEKIT_API_KEY || 'devkey';
const secret = process.env.LIVEKIT_API_SECRET || 'devsecretdevsecretdevsecret123456';

export async function createToken(identity: string, room: string) {
  const at = new AccessToken(apiKey, secret, { identity });
  at.addGrant({ roomJoin: true, room });
  return at.toJwt();
}
