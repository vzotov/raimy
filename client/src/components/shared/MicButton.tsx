'use client';
import React, { useState } from 'react';
import { useVoiceAssistant, useLocalParticipant } from '@livekit/components-react';
import classNames from 'classnames';

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
        'w-28 h-28 rounded-full flex items-center justify-center shadow-md transition-all',
        {
          'bg-surface/50 cursor-not-allowed opacity-50': disabled,
          'bg-red-500 hover:bg-red-600': isMicrophoneEnabled && !disabled,
          'bg-surface hover:bg-surface/80': !isMicrophoneEnabled && !disabled,
        },
      )}
      onClick={handleClick}
      disabled={disabled}
    >
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          x="18"
          y="10"
          width="12"
          height="20"
          rx="6"
          stroke={isMicrophoneEnabled ? '#fff' : '#888'}
          strokeWidth="2"
        />
        <path
          d="M24 38V42"
          stroke={isMicrophoneEnabled ? '#fff' : '#888'}
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path
          d="M16 34C16 37.3137 19.134 40 24 40C28.866 40 32 37.3137 32 34"
          stroke={isMicrophoneEnabled ? '#fff' : '#888'}
          strokeWidth="2"
        />
      </svg>
    </button>
  );
}
