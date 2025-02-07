#%%
import asyncio
s3_location = "s3://eum-social-bedrock-s3486f821d-iblosczk09sj/voice_977499647678898.ogg"
from transcribe import TranscribeService
transcribe_service = TranscribeService()
transcriptr = transcribe_service.transcribe(s3_location)


print ("transcript:", transcriptr)



exit()

#%%
import asyncio
import boto3
import io

# This example uses aiofile for asynchronous file reads.
# It's not a dependency of the project but can be installed
# with `pip install aiofile`.
import aiofile
a
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from amazon_transcribe.utils import apply_realtime_delay


# %%

"""
Here's an example of a custom event handler you can extend to
process the returned transcription results as needed. This
handler will simply print the text out to your interpreter.
"""


SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2
CHANNEL_NUMS = 1

# Parse S3 location
s3_bucket = s3_location.split('/')[2]
s3_key = '/'.join(s3_location.split('/')[3:])
CHUNK_SIZE = 1024 * 8
REGION = "us-east-1"


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # This handler can be implemented to handle transcriptions as needed.
        # Here's an example to get started.
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                print(alt.transcript)


async def basic_transcribe():
    # Setup up our client with our chosen AWS region
    client = TranscribeStreamingClient(region=REGION)

    # Start transcription to generate our async stream
    stream = await client.start_stream_transcription(
        language_code="es-US",
        # language_options = ["es-US", "en-US"], # no soportado en este client
        # identify_language=True,
        media_sample_rate_hz=SAMPLE_RATE,
        media_encoding="ogg-opus",
    )

    async def write_chunks():
        # Download from S3
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        audio_data = response['Body'].read()
        
        # Create a file-like object from the downloaded data
        audio_stream = io.BytesIO(audio_data)
        
        while True:
            chunk = audio_stream.read(CHUNK_SIZE)
            if not chunk:
                break
            await stream.input_stream.send_audio_event(audio_chunk=chunk)
            await asyncio.sleep(CHUNK_SIZE / (SAMPLE_RATE * BYTES_PER_SAMPLE * CHANNEL_NUMS))
            
        await stream.input_stream.end_stream()

    # Instantiate our handler and start processing events
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(write_chunks(), handler.handle_events())

# %%
loop = asyncio.get_event_loop()
loop.run_until_complete(basic_transcribe())
loop.close()
# %%
