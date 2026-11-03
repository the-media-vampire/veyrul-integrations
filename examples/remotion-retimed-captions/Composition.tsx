import React from 'react';
import {AbsoluteFill, Composition, OffthreadVideo, Sequence, registerRoot, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

type Word = {text: string; start_us: number; end_us: number; source_index: number; cut_index?: number};
type Segment = {cut_index: number; from: number; durationInFrames: number; trimBefore: number; sourceFrames: number; playbackRate: number};
type Timing = {label: string; fps: number; durationInFrames: number; words: Word[]; sourceWords: Word[]; segments: Segment[]; activeByFrame: (number | null)[]; unrepresentedIndices: number[]};
type Props = {timing: Timing};
const colors = ['#184b70', '#176451', '#514477', '#774b2a', '#5e3155', '#23566c', '#535e2d'];
const base: React.CSSProperties = {backgroundColor: '#11151c', color: '#f5f4ef', fontFamily: 'Arial, sans-serif'};

// Original silent diagnostic footage. It is not a transcription or customer video.
const Source: React.FC<Props> = ({timing}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const word = timing.sourceWords.find(w => w.start_us * fps <= frame * 1000000 && frame * 1000000 < w.end_us * fps);
  return <AbsoluteFill style={{...base, backgroundColor: word ? colors[word.source_index % colors.length] : '#11151c', alignItems: 'center'}}>
    <div style={{position: 'absolute', top: 210, fontSize: 22, letterSpacing: 5}}>SOURCE TIMELINE</div>
    <div style={{position: 'absolute', top: 300, fontSize: 70, fontWeight: 700}}>{word?.text ?? '—'}</div>
    <div style={{position: 'absolute', top: 420, fontSize: 24, opacity: 0.8}}>{(frame / fps).toFixed(2)} s</div>
    <div style={{position: 'absolute', top: 490, fontSize: 18, opacity: 0.7}}>Original silent timing fixture</div>
  </AbsoluteFill>;
};

const Edited: React.FC<Props> = ({timing}) => {
  const frame = useCurrentFrame();
  const active = timing.activeByFrame[frame];
  const word = active == null ? null : timing.words[active];
  const segment = timing.segments.find(s => s.from <= frame && frame < s.from + s.durationInFrames);
  return <AbsoluteFill style={base}>
    {timing.segments.map(s => <Sequence key={s.cut_index} from={s.from} durationInFrames={s.durationInFrames}>
      <OffthreadVideo src={staticFile('source.mp4')} trimBefore={s.trimBefore} durationInFrames={s.sourceFrames}
        playbackRate={s.playbackRate} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </Sequence>)}
    <div style={{position: 'absolute', inset: '600px 0 0', background: 'linear-gradient(transparent, #11151c 16%)'}} />
    <div style={{position: 'absolute', left: 54, right: 54, top: 66, display: 'flex', justifyContent: 'space-between', fontSize: 18, letterSpacing: 2}}>
      <span>EDIT-AWARE CAPTIONS</span><span>{segment ? `${segment.playbackRate}×` : ''}</span>
    </div>
    <div style={{position: 'absolute', top: 652, left: 50, right: 50, textAlign: 'center', fontSize: 20, color: '#b3b8c2'}}>{timing.label}</div>
    {word && <div style={{position: 'absolute', top: 714, left: 50, width: 620, height: 124, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 22, background: '#edda60', color: '#11151c', fontSize: 66, fontWeight: 700, whiteSpace: 'nowrap'}}>{word.text}</div>}
    <div style={{position: 'absolute', left: 70, right: 70, top: 896, textAlign: 'center', fontSize: 25, lineHeight: 1.5}}>
      Keep the edit.<br/>Keep the words in sync.
    </div>
    <div style={{position: 'absolute', left: 54, right: 54, bottom: 94, display: 'flex', justifyContent: 'space-between', color: '#a5acb8', fontSize: 16}}>
      <span>Saved timing code → Remotion</span><span>Veyrul example</span>
    </div>
    {timing.unrepresentedIndices.length > 0 && <div style={{position: 'absolute', bottom: 30, left: 54, right: 54, fontSize: 18, color: '#ffac90'}}>Some word occurrences have no visible frame. Inspect unrepresentedIndices.</div>}
  </AbsoluteFill>;
};

const empty: Timing = {label: 'Prepared edit', fps: 30, durationInFrames: 1, words: [], sourceWords: [], segments: [], activeByFrame: [null], unrepresentedIndices: []};
const Root = () => <>
  <Composition id="Source" component={Source} width={720} height={1280} fps={30} durationInFrames={180}
    defaultProps={{timing: empty}} calculateMetadata={({props}) => ({fps: props.timing.fps, durationInFrames: props.timing.fps * 6})} />
  <Composition id="Edited" component={Edited} width={720} height={1280} fps={30} durationInFrames={1}
    defaultProps={{timing: empty}} calculateMetadata={({props}) => ({fps: props.timing.fps, durationInFrames: props.timing.durationInFrames})} />
</>;
registerRoot(Root);
