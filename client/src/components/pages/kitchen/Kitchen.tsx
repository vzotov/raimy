'use client';
import React, { useState, useEffect, useCallback } from 'react';
import classNames from 'classnames';
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
import AgentTranscription from '@/components/shared/AgentTranscription';
import IngredientList, { Ingredient } from '@/components/shared/IngredientList';
import TimerList from '@/components/shared/TimerList';
import KitchenDebugPanel from './KitchenDebugPanel';
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
  const [timers, setTimers] = useState<
    Array<{
      duration: number;
      label: string;
      started_at: number;
    }>
  >([]);
  const [recipeName, setRecipeName] = useState<string>('');

  const [ingredients, setIngredients] = useState<Array<Ingredient>>([]);

  // Handle SSE events
  const handleSSEMessage = useCallback((event: { type: string; data: Record<string, unknown> }) => {
    if (event.type === 'timer_set') {
      const timerData = event.data as unknown as {
        duration: number;
        label: string;
        started_at: number;
      };
      setTimers((prev) => [...prev, timerData]);
      console.log('Timer set via SSE:', timerData);
    } else if (event.type === 'recipe_name') {
      const recipeData = event.data as unknown as { recipe_name: string; timestamp: number };
      setRecipeName(recipeData.recipe_name);
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
    <div className={classNames('flex flex-col flex-1')}>
      <RoomAudioRenderer />

      {/* Header - Recipe Name */}
      <div className={classNames('transition-[height,opacity] duration-300 ease-in-out overflow-hidden', {
        'h-0 opacity-0': !recipeName,
        'h-auto opacity-100': recipeName,
      })}>
        <div className={classNames('p-4')}>
          <h2 className={classNames('text-center text-xl font-semibold')}>
            {recipeName}
          </h2>
        </div>
      </div>

      {/* Main Console - Takes all available space */}
      <div className={classNames('flex-1 flex flex-col pt-4')}>
        <div className={classNames('flex flex-row gap-4 transition-[height,opacity] duration-300 ease-in-out overflow-hidden max-h-[40vh] px-4', {
          'h-0 opacity-0': ingredients.length === 0 && timers.length === 0,
          'h-auto opacity-100': ingredients.length > 0 || timers.length > 0,
        })}>
          <div className={classNames('transition-[height,opacity,margin] duration-300 ease-in-out', {
            'h-0 opacity-0 mb-0': ingredients.length === 0,
            'h-auto opacity-100 mb-4 flex-1': ingredients.length > 0,
          })}>
            {ingredients.length > 0 && <IngredientList ingredients={ingredients} />}
          </div>

          <div className={classNames('transition-[height,opacity,margin] duration-300 ease-in-out overflow-y-auto', {
            'h-0 opacity-0 mb-0': timers.length === 0,
            'h-auto opacity-100 mb-4 flex-1': timers.length > 0,
          })}>
            {timers.length > 0 && <TimerList timers={timers} />}
          </div>
        </div>

        <div className={classNames('flex flex-1 items-center justify-center px-4')}>
          <AgentTranscription
            message={agentMessage}
            audioTrack={voiceAssistant?.audioTrack}
          />
        </div>
      </div>

      {/* Footer */}
      <div className={classNames('bg-surface rounded-t-2xl p-4 mx-4 transition-[height,padding] duration-300 ease-in-out overflow-hidden')}>
        <div className={classNames('transition-[height,opacity,margin] duration-300 ease-in-out', {
          'h-0 opacity-0 mb-0': !userMessage,
          'h-auto opacity-100 mb-4': userMessage,
        })}>
          {userMessage && (
            <div className={classNames('text-center')}>
              <p className={classNames('text-base italic text-text/80')}>
                &ldquo;{userMessage}&rdquo;
              </p>
            </div>
          )}
        </div>

        <div className={classNames('flex justify-center')}>
          <MicButton disabled={connectionState !== 'connected'} />
        </div>
      </div>

      {/* Debug Panel - Only in development */}
      {process.env.NODE_ENV === 'development' && (
        <KitchenDebugPanel
          connectionState={connectionState}
          assistantState={assistantState}
          onSetIngredients={setIngredients}
          onSetTimers={setTimers}
          onSetUserMessage={setUserMessage}
          onSetRecipeName={setRecipeName}
        />
      )}
    </div>
  );
}
