/**
 * audioProcessor.ts
 * ─────────────────
 * Real Audio Processing Utilities for NEXORA:
 * - 48kHz/44.1kHz -> 16kHz Float32 Resampling
 * - Float32 -> Int16 PCM conversion
 * - Mono PCM16 WAVE container encoding
 * - Real-time RMS Gain (dB) calculation
 */

/**
 * Calculates RMS volume and converts to dBFS (-60 dB to 0 dB)
 */
export function calculateRMSAndDb(analyser: AnalyserNode): { rms: number; db: number } {
  const timeData = new Float32Array(analyser.fftSize);
  analyser.getFloatTimeDomainData(timeData);

  let sumSquares = 0;
  for (let i = 0; i < timeData.length; i++) {
    sumSquares += timeData[i] * timeData[i];
  }
  const rms = Math.sqrt(sumSquares / (timeData.length || 1));
  const db = rms > 0.00001 ? Math.max(-60, Math.min(0, Math.round(20 * Math.log10(rms)))) : -60;
  return { rms, db };
}

/**
 * Resamples Float32 audio array from inputSampleRate down to targetSampleRate (default 16000 Hz)
 */
export function resampleFloat32(
  inputData: Float32Array,
  fromSampleRate: number,
  toSampleRate: number = 16000
): Float32Array {
  if (!inputData || inputData.length === 0 || fromSampleRate === toSampleRate) {
    return inputData;
  }
  const ratio = fromSampleRate / toSampleRate;
  const newLength = Math.floor(inputData.length / ratio);
  const result = new Float32Array(newLength);

  for (let i = 0; i < newLength; i++) {
    const originPos = i * ratio;
    const indexFloor = Math.floor(originPos);
    const indexCeil = Math.min(inputData.length - 1, indexFloor + 1);
    const fraction = originPos - indexFloor;

    result[i] = (1 - fraction) * inputData[indexFloor] + fraction * inputData[indexCeil];
  }
  return result;
}

/**
 * Converts Float32 audio samples [-1.0, 1.0] to 16-bit PCM Int16Array
 */
export function float32ToInt16PCM(float32Data: Float32Array): Int16Array {
  const pcm16 = new Int16Array(float32Data.length);
  for (let i = 0; i < float32Data.length; i++) {
    const s = Math.max(-1, Math.min(1, float32Data[i]));
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return pcm16;
}

/**
 * Wraps 16kHz Int16 PCM samples into a standalone 16-bit Mono WAV container Blob
 */
export function encodeWAV(pcm16Samples: Int16Array, sampleRate: number = 16000, numChannels: number = 1): Blob {
  const dataByteLength = pcm16Samples.length * 2;
  const buffer = new ArrayBuffer(44 + dataByteLength);
  const view = new DataView(buffer);

  /* RIFF chunk descriptor */
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + dataByteLength, true);
  writeString(view, 8, 'WAVE');

  /* fmt sub-chunk */
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
  view.setUint16(20, 1, true);  // AudioFormat (1 for PCM)
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * 2, true); // ByteRate
  view.setUint16(32, numChannels * 2, true);              // BlockAlign
  view.setUint16(34, 16, true);                           // BitsPerSample

  /* data sub-chunk */
  writeString(view, 36, 'data');
  view.setUint32(40, dataByteLength, true);

  /* Write PCM samples */
  const bytesView = new Uint8Array(buffer, 44);
  const pcmBytes = new Uint8Array(pcm16Samples.buffer, pcm16Samples.byteOffset, dataByteLength);
  bytesView.set(pcmBytes);

  return new Blob([buffer], { type: 'audio/wav' });
}

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}
