'use client';
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useMultibandTrackVolume, TrackReference } from '@livekit/components-react';

const UPDATE_INTERVAL = 100;
const BANDS = 10;
const MIN_RADIUS_RATIO = 0.05;
const MAX_RADIUS_RATIO = 1;
const MIDPOINT_NORMALIZATION = 0.2;

interface VoiceVisualizationProps {
  audioTrack?: TrackReference;
  width?: number;
  height?: number;
  className?: string;
}

interface RadialDataPoint {
  angle: number;
  r: number;
  value: number;
}

const VoiceVisualization: React.FC<VoiceVisualizationProps> = ({
  audioTrack,
  width = 200,
  height = 200,
  className = '',
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  // Use the multiband track volume hook with the provided audio track
  const volumes = useMultibandTrackVolume(audioTrack, {
    bands: BANDS,
    updateInterval: UPDATE_INTERVAL,
    loPass: 100,
    hiPass: 200,
  });

  // Generate random values when audioTrack is undefined
  // const [randomVolumes, setRandomVolumes] = useState<number[]>([]);

  // useEffect(() => {
  //   if (!audioTrack) {
  //     const generateRandomVolumes = () => {
  //       const newVolumes = Array.from({ length: BANDS }, () => Math.random());
  //       setRandomVolumes(newVolumes);
  //     };

  //     // Generate initial random values
  //     generateRandomVolumes();

  //     // Update random values
  //     const interval = setInterval(generateRandomVolumes, UPDATE_INTERVAL);
  //     return () => clearInterval(interval);
  //   } else {
  //     setRandomVolumes([]);
  //   }
  // }, [audioTrack]);

  // Use volumes from audio track or zeros when no audio
  const displayVolumes = audioTrack ? volumes : Array.from({ length: BANDS }, () => 0);

  // D3 update function
  const updateVisualization = React.useCallback(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);

    // Create trail effect filter only once
    if (svg.select('defs').empty()) {
      const defs = svg.append('defs');
      const trailFilter = defs
        .append('filter')
        .attr('id', 'trail-filter')
        .attr('x', '-50%')
        .attr('y', '-50%')
        .attr('width', '200%')
        .attr('height', '200%');

      // Create motion blur effect
      trailFilter.append('feGaussianBlur').attr('stdDeviation', '1').attr('result', 'blur1');

      trailFilter.append('feGaussianBlur').attr('stdDeviation', '2').attr('result', 'blur2');

      trailFilter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'blur3');

      // Merge the blurred layers with decreasing opacity
      const merge1 = trailFilter.append('feMerge');
      merge1.append('feMergeNode').attr('in', 'blur3');
      merge1.append('feMergeNode').attr('in', 'blur2');
      merge1.append('feMergeNode').attr('in', 'blur1');
      merge1.append('feMergeNode').attr('in', 'SourceGraphic');
    }

    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;

    // Create radial area chart data
    const numDots = displayVolumes?.length || BANDS;
    const angleStep = (2 * Math.PI) / numDots;

    // Create data points with angle and radius
    const originalData = Array.from({ length: numDots }, (_, i) => {
      const angle = i * angleStep;
      const value = displayVolumes?.[i] || 0;
      const normalizedValue = Math.max(0, Math.min(1, value));
      const r =
        radius * (MIN_RADIUS_RATIO + normalizedValue * (MAX_RADIUS_RATIO - MIN_RADIUS_RATIO));
      return { angle, r, value: normalizedValue };
    });

    // Double the data points by inserting 0.2 values between existing points
    const data = [];
    for (let i = 0; i < originalData.length; i++) {
      // Add original point
      data.push(originalData[i]);

      // Add intermediate point with 0.2 value
      const nextIndex = (i + 1) % originalData.length;
      const currentAngle = originalData[i].angle;
      const nextAngle = originalData[nextIndex].angle;

      // Handle wrap-around for the last point
      let midAngle;
      if (i === originalData.length - 1) {
        // Last point: interpolate to first point + 2π
        midAngle = currentAngle + (2 * Math.PI - currentAngle) / 2;
      } else {
        midAngle = currentAngle + (nextAngle - currentAngle) / 2;
      }

      // Calculate average of adjacent dots
      const currentValue = originalData[i].value;
      const nextValue = originalData[nextIndex].value;
      const averageValue = (currentValue + nextValue) / 2;

      // Normalize by midpoint constant
      const normalizedValue = averageValue * MIDPOINT_NORMALIZATION;
      const midR =
        radius * (MIN_RADIUS_RATIO + normalizedValue * (MAX_RADIUS_RATIO - MIN_RADIUS_RATIO));
      data.push({ angle: midAngle, r: midR, value: normalizedValue });
    }

    // Create radial line generator
    const lineGenerator = d3
      .lineRadial<RadialDataPoint>()
      .angle((d) => d.angle)
      .radius((d) => d.r)
      .curve(d3.curveCardinalClosed.tension(0.3));

    // Update line with transitions
    const line = svg.selectAll('.radial-line').data([data]);

    // Remove old line
    line.exit().remove();

    // Add new line
    const lineEnter = line
      .enter()
      .append('path')
      .attr('class', 'radial-line')
      .attr('fill', 'none')
      .attr('stroke', 'var(--color-primary)')
      .attr('stroke-width', 2);

    // Merge enter and update selections
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const lineUpdate = lineEnter.merge(line as any);

    // Update line with transitions
    lineUpdate
      .transition()
      .duration(100)
      .ease(d3.easeCubicInOut)
      .attr('d', (d: RadialDataPoint[]) => lineGenerator(d))
      .attr('transform', `translate(${centerX}, ${centerY})`);
  }, [displayVolumes, width, height]);

  useEffect(() => {
    updateVisualization();
  }, [displayVolumes, width, height, updateVisualization]);

  return (
    <div
      className={`flex items-center justify-center ${className}`}
      style={{ filter: 'blur(10px)' }}
    >
      <svg
        style={{
          filter: 'url(#trail-filter)',
        }}
        ref={svgRef}
        width={width}
        height={height}
      />
    </div>
  );
};

export default VoiceVisualization;
