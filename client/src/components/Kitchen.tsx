'use client';
import React, { useState, useEffect, useCallback } from 'react';
import {
  useConnectionState,
  useParticipants,
  useVoiceAssistant,
  useTranscriptions,
  useLocalParticipant,
  RoomAudioRenderer,
} from '@livekit/components-react';
import { LocalParticipant, RemoteParticipant } from 'livekit-client';
import MicButton from '@/components/MicButton';
import { useSSE } from '@/hooks/useSSE';

export default function Kitchen() {
  const [userMessage, setUserMessage] = useState(''); // User transcriptions
  const [agentMessage, setAgentMessage] = useState('Waiting for Raimy to come to the kitchen...'); // Agent transcriptions
  const connectionState = useConnectionState();
  const participants = useParticipants();
  const [assistantState, setAssistantState] = useState('idle');
  const voiceAssistant = useVoiceAssistant();
  const transcriptions = useTranscriptions();
  const { localParticipant } = useLocalParticipant();
  const [timers, setTimers] = useState<Array<{ duration: number; label: string; started_at: number }>>([]);

  // Handle SSE events
  const handleSSEMessage = useCallback((event: { type: string; data: Record<string, unknown> }) => {
    if (event.type === 'timer_set') {
      const timerData = event.data as unknown as { duration: number; label: string; started_at: number };
      setTimers(prev => [...prev, timerData]);
      console.log('Timer set via SSE:', timerData);
    }
  }, []);

  useSSE({
    onMessage: handleSSEMessage,
  });

  // Store user and agent instances
  const [user, setUser] = useState<LocalParticipant | null>(null);
  const [agent, setAgent] = useState<RemoteParticipant | null>(null);

  // Get user and agent instances when connected
  useEffect(() => {
    if (connectionState === 'connected' && participants.length > 0) {
      // Set local participant as user
      setUser(localParticipant);

      // Find agent participant (only remote participants)
      const agentParticipant = participants.find(
        (p) => p.identity.includes('agent') || p.identity.includes('assistant'),
      ) as RemoteParticipant | undefined;
      setAgent(agentParticipant || null);

      console.log('User:', localParticipant);
      console.log('Agent:', agentParticipant);
    }
  }, [connectionState, participants, localParticipant]);

  // Update messages from transcriptions
  useEffect(() => {
    if (transcriptions.length > 0 && user && agent) {
      const lastTranscription = transcriptions[transcriptions.length - 1];
      console.log('Transcription data:', lastTranscription);
      console.log('Transcription keys:', Object.keys(lastTranscription));

      // Check if transcription is from user or agent by comparing identities
      const transcriptionIdentity = lastTranscription.participantInfo?.identity;

      if (transcriptionIdentity === user.identity) {
        setUserMessage(lastTranscription.text);
      } else if (transcriptionIdentity === agent.identity) {
        setAgentMessage(lastTranscription.text);
      }
    }
  }, [transcriptions, user, agent]);

  // Track assistant state from voice assistant
  useEffect(() => {
    if (voiceAssistant) {
      console.log('Voice assistant:', voiceAssistant);
      // You can access voiceAssistant.state, voiceAssistant.isListening, etc.
      setAssistantState(voiceAssistant.state || 'active');
    } else {
      setAssistantState('not_found');
    }
  }, [voiceAssistant]);

  return (
    <div className="flex flex-col justify-between items-center min-h-screen py-8 bg-white">
      {/* Room Audio Renderer - renders audio from all participants */}
      <RoomAudioRenderer />

      {/* Debug indicators */}
      <div className="w-full flex justify-between px-4 mb-2 text-xs text-gray-500">
        <div>
          Connection:{' '}
          <span className={connectionState === 'connected' ? 'text-green-600' : 'text-red-600'}>
            {connectionState}
          </span>
        </div>
        <div>
          Assistant: <span className="text-blue-600">{assistantState}</span>
        </div>
      </div>
      <div className="text-center">
        <h2 className="font-semibold text-lg sm:text-xl">{agentMessage}</h2>
      </div>

      {/* Timer Display */}
      {timers.length > 0 && (
        <div className="w-full max-w-md mx-auto mb-4">
          <h3 className="text-lg font-semibold mb-2">Active Timers</h3>
          <div className="space-y-2">
            {timers.map((timer, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div>
                  <p className="font-medium">{timer.label}</p>
                  <p className="text-sm text-gray-600">
                    {Math.floor(timer.duration / 60)}:{(timer.duration % 60).toString().padStart(2, '0')}
                  </p>
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {Math.floor(timer.duration / 60)}:{(timer.duration % 60).toString().padStart(2, '0')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="flex flex-col items-center">
        {userMessage && <div className="italic mb-4 text-xl">&ldquo;{userMessage}&rdquo;</div>}
        <MicButton disabled={connectionState !== 'connected'} />
      </div>
    </div>
  );
}
