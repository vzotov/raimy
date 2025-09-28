import React from 'react';
import VoiceVisualization from './VoiceVisualization';
import { TrackReference } from '@livekit/components-react';

interface AgentTranscriptionProps {
  message: string;
  audioTrack?: TrackReference;
}

export default function AgentTranscription({ message, audioTrack }: AgentTranscriptionProps) {
  return (
    <div className="relative">
      {/* Voice Visualization - positioned behind text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <VoiceVisualization audioTrack={audioTrack} width={200} height={200} />
      </div>
      
      {/* Agent text overlay */}
      <h2 className="relative z-10 text-center text-lg font-semibold sm:text-xl">
        {message}
      </h2>
    </div>
  );
} 