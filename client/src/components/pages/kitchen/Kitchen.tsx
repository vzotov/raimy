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
import TimerList, { Timer } from '@/components/shared/TimerList';
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
    Array<Timer>
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
      setTimers((prev) => [...prev, {
        duration: timerData.duration,
        label: timerData.label,
        startedAt: Date.now(),
      }]);
      console.log('Timer set via SSE:', timerData);
    } else if (event.type === 'recipe_name') {
      const recipeData = event.data as unknown as { recipe_name: string; timestamp: number };
      setRecipeName(recipeData.recipe_name);
      console.log('Recipe name received via SSE:', recipeData);
    } else if (event.type === 'ingredients') {
      const ingredientsData = event.data as unknown as { ingredients: Array<Ingredient>; action?: string; timestamp: number };
      console.log('Ingredients data received via SSE:', ingredientsData);
      
      const action = ingredientsData.action || 'set'; // Default to 'set' for backward compatibility
      
      if (action === 'set') {
        // Set complete ingredients list (replace all)
        const formattedIngredients: Ingredient[] = ingredientsData.ingredients.map((ingredient, index) => ({
          name: ingredient.name,
          amount: ingredient.amount,
          unit: ingredient.unit,
          highlighted: ingredient.highlighted || false,
          used: ingredient.used || false,
        }));
        setIngredients(formattedIngredients);
        console.log('Ingredients set via SSE:', formattedIngredients);
      } else if (action === 'update') {
        // Update existing ingredients by matching name, or add new ones
        setIngredients((prevIngredients) => {
          const updatedIngredients = [...prevIngredients];
          
          ingredientsData.ingredients.forEach((newIngredient) => {
            const existingIndex = updatedIngredients.findIndex(
              (existing) => existing.name === newIngredient.name
            );
            
            if (existingIndex >= 0) {
              // Update existing ingredient with new data
              updatedIngredients[existingIndex] = {
                ...updatedIngredients[existingIndex],
                ...newIngredient,
              };
            } else {
              // Add new ingredient
              updatedIngredients.push({
                name: newIngredient.name,
                amount: newIngredient.amount,
                unit: newIngredient.unit,
                highlighted: newIngredient.highlighted || false,
                used: newIngredient.used || false,
              });
            }
          });
          
          return updatedIngredients;
        });
        
        console.log('Ingredients updated via SSE:', ingredientsData.ingredients);
      }
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
    <div className={classNames('flex flex-1 flex-col w-full max-w-4xl mx-auto')}>
      <RoomAudioRenderer />

      {/* Header - Recipe Name */}
      <div
        className={classNames('overflow-hidden transition-all duration-300 ease-in-out', {
          'h-0 opacity-0': !recipeName,
          'h-auto opacity-100': recipeName,
        })}
      >
        <div className={classNames('p-4')}>
          <h2 className={classNames('text-center text-xl font-semibold line-clamp-2')}>{recipeName}</h2>
        </div>
      </div>

      {/* Main Console - Takes all available space */}
      <div className={classNames('flex flex-1 flex-col')}>
        <div
          className={classNames(
            'flex flex-col gap-4 overflow-hidden px-4 transition-[height,opacity] duration-300 ease-in-out',
            {
              'h-0 opacity-0': ingredients.length === 0 && timers.length === 0,
              'h-auto opacity-100': ingredients.length > 0 || timers.length > 0,
            },
          )}
        >
          <div
            className={classNames('transition-all duration-300 ease-in-out', {
              'h-0 opacity-0': timers.length === 0,
              'h-auto opacity-100': timers.length > 0,
            })}
          >
            {timers.length > 0 && <TimerList timers={timers} />}
          </div>
          <div
            className={classNames('flex-1 transition-all duration-300 ease-in-out', {
              'h-0 opacity-0': ingredients.length === 0,
              'h-auto opacity-100': ingredients.length > 0,
            })}
          >
            {ingredients.length > 0 && <IngredientList ingredients={ingredients} />}
          </div>
        </div>

        <div className={classNames('flex flex-1 items-center justify-center px-4 min-w-0')}>
          <div className={classNames('w-full max-w-2xl')}>
            <AgentTranscription message={agentMessage} audioTrack={voiceAssistant?.audioTrack} />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div
        className={classNames(
          'mx-4 overflow-hidden rounded-t-2xl bg-surface p-4 transition-[height,padding] duration-300 ease-in-out',
        )}
      >
        <div
          className={classNames('transition-all duration-300 ease-in-out', {
            'mb-0 h-0 opacity-0': !userMessage,
            'mb-4 h-auto opacity-100': userMessage,
          })}
        >
          {userMessage && (
            <div className={classNames('text-center')}>
              <p className={classNames('text-base text-text/80 italic')}>
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
