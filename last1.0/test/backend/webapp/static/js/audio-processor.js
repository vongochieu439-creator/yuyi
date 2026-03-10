/**
 * AudioWorklet 处理器 - 浏览器端音频采集
 * 将麦克风输入的 Float32 音频转换为 PCM16 并通过 port 发送
 */
class AudioCaptureProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this._bufferSize = 2400; // 100ms at 24kHz
        this._buffer = new Float32Array(this._bufferSize);
        this._offset = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (!input || !input[0]) return true;

        const samples = input[0];
        for (let i = 0; i < samples.length; i++) {
            this._buffer[this._offset++] = samples[i];
            if (this._offset >= this._bufferSize) {
                // 转换为 PCM16
                const pcm16 = new Int16Array(this._bufferSize);
                for (let j = 0; j < this._bufferSize; j++) {
                    const s = Math.max(-1, Math.min(1, this._buffer[j]));
                    pcm16[j] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
                this._buffer = new Float32Array(this._bufferSize);
                this._offset = 0;
            }
        }
        return true;
    }
}

registerProcessor('audio-capture', AudioCaptureProcessor);
