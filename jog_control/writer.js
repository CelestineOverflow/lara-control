import fs from 'fs';
class Writer {
 /**
  * @param {string} filePath   Path to the output file
  * @param {object} [opts]
  * @param {string} [opts.flags='a']           fs flags (usually 'a' for append)
  * @param {string} [opts.encoding='utf8']     file encoding
  * @param {number} [opts.highWaterMark=64*1024] internal stream buffer size
  * @param {number} [opts.flushInterval=500]   ms between automatic flushes
  * @param {number} [opts.maxBufferLength=64*1024] flush once buffer reaches this many characters
  */
 constructor(filePath, opts = {}) {
   const {
     flags = 'w',
     encoding = 'utf8',
     highWaterMark = 64 * 1024,
     flushInterval = 500,
     maxBufferLength = 64 * 1024
   } = opts;
   this.stream = fs.createWriteStream(filePath, { flags, encoding, highWaterMark });
   this.buffer = '';
   this.maxBufferLength = maxBufferLength;
   // auto-flush timer
   this._interval = setInterval(() => this.flush(), flushInterval);
   this.stream.on('error', err => {
     console.error('Writer stream error:', err);
   });
 }
 /**
  * Queue up some data to write. Data is a plain string;
  * you control newlines if you need them.
  * @param {string} data
  */
 write(data) {
   this.buffer += data;
   if (this.buffer.length >= this.maxBufferLength) {
     this.flush();
   }
 }
 /**
  * Flush buffered data to disk immediately.
  */
 flush() {
   if (!this.buffer) return;
   this.stream.cork();
   const ok = this.stream.write(this.buffer);
   this.stream.uncork();
   this.buffer = '';
   // handle back-pressure if needed
   if (!ok) {
     this.stream.once('drain', () => {
       // you could log or emit an event here if desired
     });
   }
 }
 /**
  * Cleanly shut down: flush any remaining data and close the stream.
  */
 end() {
   clearInterval(this._interval);
   this.flush();
   this.stream.end();
   //delete the file
   
 }
}
export default Writer;