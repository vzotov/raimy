'use client';
import React from 'react';
import { useVoiceAssistant, useLocalParticipant } from '@livekit/components-react';
import classNames from 'classnames';
import { MicrophoneIcon } from '@/components/icons';

interface MicButtonProps {
  disabled?: boolean;
}

export default function MicButton({ disabled = false }: MicButtonProps) {
  const voiceAssistant = useVoiceAssistant();
  const { localParticipant, microphoneTrack, isMicrophoneEnabled } = useLocalParticipant();

  const handleClick = async () => {
    if (disabled || !localParticipant) return;

    try {
      if (isMicrophoneEnabled) {
        // Disable mic - unpublish audio track
        const mediaStreamTrack = microphoneTrack?.track?.mediaStreamTrack;
        if (mediaStreamTrack) {
          await localParticipant.unpublishTrack(mediaStreamTrack);
        }
        await localParticipant.setMicrophoneEnabled(false);
        console.log('Microphone disabled and unpublished');
      } else {
        // Enable mic - publish audio track
        await localParticipant.setMicrophoneEnabled(true);
        console.log('Microphone enabled');
      }
    } catch (error) {
      console.error('Error toggling microphone:', error);
    }
  };

  return (
    <button
      className={classNames(
        'w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-all',
        {
          'opacity-30': disabled,
          'bg-red-500 hover:bg-red-600 hover:scale-105': isMicrophoneEnabled && !disabled,
          'bg-primary hover:bg-primary-hover hover:scale-105': !isMicrophoneEnabled && !disabled,
        },
        // Base background color when disabled
        disabled ? (isMicrophoneEnabled ? 'bg-red-500' : 'bg-primary') : '',
      )}
      onClick={handleClick}
      disabled={disabled}
    >
      <MicrophoneIcon className="w-6 h-6 text-white" />
    </button>
  );
}
