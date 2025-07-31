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
import MicButton from '@/components/shared/MicButton';
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
  const [currentRecipe, setCurrentRecipe] = useState<string>('');

  // Handle SSE events
  const handleSSEMessage = useCallback((event: { type: string; data: Record<string, unknown> }) => {
    if (event.type === 'timer_set') {
      const timerData = event.data as unknown as { duration: number; label: string; started_at: number };
      setTimers(prev => [...prev, timerData]);
      console.log('Timer set via SSE:', timerData);
    } else if (event.type === 'recipe_name') {
      const recipeData = event.data as unknown as { recipe_name: string; timestamp: number };
      setCurrentRecipe(recipeData.recipe_name);
      console.log('Recipe name received via SSE:', recipeData);
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
    <div className="relative flex flex-col justify-between items-center min-h-screen py-8 bg-background">
      {/* Room Audio Renderer - renders audio from all participants */}
      <RoomAudioRenderer />

      {/* Recipe Name Display */}
      <div className="w-full max-w-md mx-auto mb-4">
        <h2 className="text-xl font-semibold text-center">{currentRecipe || ''}</h2>
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
              <div key={index} className="flex items-center justify-between p-3 bg-timer-bg rounded-lg">
                <div>
                  <p className="font-medium">{timer.label}</p>
                  <p className="text-sm text-text/70">
                    {Math.floor(timer.duration / 60)}:{(timer.duration % 60).toString().padStart(2, '0')}
                  </p>
                </div>
                <div className="text-2xl font-bold text-primary">
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

      {/* Debug indicators */}
      <div className="absolute bottom-4 left-4 flex space-x-2">
        <div className={`w-3 h-3 rounded-full ${connectionState === 'connected' ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <div className="w-3 h-3 rounded-full bg-primary"></div>
      </div>
    </div>
  );
}
