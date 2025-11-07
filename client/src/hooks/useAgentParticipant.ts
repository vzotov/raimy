import { useEffect } from 'react';
import { useVoiceAssistant } from '@livekit/components-react';
import { RemoteParticipant } from 'livekit-client';

/**
 * Custom hook to get the agent participant from LiveKit room.
 * Works for both voice and text-based agents.
 *
 * @returns The agent RemoteParticipant or undefined if not found
 */
export function useAgentParticipant(): RemoteParticipant | undefined {
  const voiceAssistant = useVoiceAssistant();

  // Debug logging
  useEffect(() => {
    console.log('[useAgentParticipant] voiceAssistant:', voiceAssistant);
    console.log('[useAgentParticipant] voiceAssistant.agent:', voiceAssistant.agent);
    console.log('[useAgentParticipant] voiceAssistant.state:', voiceAssistant.state);
  }, [voiceAssistant]);

  return voiceAssistant.agent;
}
