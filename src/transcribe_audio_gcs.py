# https://cloud.ibm.com/apidocs/speech-to-text?code=python
# https://github.com/watson-developer-cloud/python-sdk/blob/master/examples/text_to_speech_v1.py

from google.cloud import speech


def transcribe_audio_gcs(
    gcs_uri: str,
    model: str,
) -> speech.RecognizeResponse:
    """Transcribe the given audio file asynchronously with
    the selected model."""

    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        model=model,
    )

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=90)

    for i, result in enumerate(response.results):
        alternative = result.alternatives[0]
        print("-" * 20)
        print(f"First alternative of result {i}")
        print(f"Transcript: {alternative.transcript}")

    return response
