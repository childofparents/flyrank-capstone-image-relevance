import os
import logging
import google.generativeai as genai
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import ImageRecord, ImageTagRecord, CostLog, ImageStatus
from metadata_schema import ImageMetadata

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini Flash
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
VISION_MODEL = "gemini-1.5-flash"
CONFIDENCE_THRESHOLD = 0.85


def log_cost_entry(db: Session, model: str, operation: str, status: str, image_id: int = None, cost: float = 0.0):
    """Persists a per-call cost entry directly into the PostgreSQL cost_logs table."""
    try:
        cost_entry = CostLog(
            model_name=model,
            operation=operation,
            cost=cost,
            status=status,
            image_id=image_id
        )
        db.add(cost_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log cost entry: {e}")


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,))
)
def call_gemini_vision(image_path: str) -> ImageMetadata:
    """
    Sends the image file to Gemini Flash, enforcing structured JSON output
    and validating against the ImageMetadata schema.
    """
    uploaded_file = genai.upload_file(path=image_path)
    model = genai.GenerativeModel(VISION_MODEL)

    prompt = """
    Analyze this image carefully. Extract the primary subject, broad category, 
    a list of visual attributes, a descriptive caption, and your confidence score (0.0 to 1.0).
    Return the result strictly as a valid JSON object matching the requested schema.
    """

    response = model.generate_content(
        [uploaded_file, prompt],
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
        )
    )

    # Parse & validate strictly against Pydantic schema
    return ImageMetadata.model_validate_json(response.text)


def process_single_image(db: Session, image_record: ImageRecord):
    """Processes an individual image, validates output, and updates database records."""
    image_path = image_record.filepath

    if not os.path.exists(image_path):
        logger.error(f"File not found: {image_path}")
        image_record.status = ImageStatus.FAILED
        log_cost_entry(db, VISION_MODEL, "vision_classification", "FILE_NOT_FOUND", image_id=image_record.id)
        db.commit()
        return

    try:
        metadata: ImageMetadata = call_gemini_vision(image_path)

        # Log successful AI call cost
        log_cost_entry(db, VISION_MODEL, "vision_classification", "SUCCESS", image_id=image_record.id, cost=0.0)

        # Confidence Gate: flag low-confidence predictions instead of guessing
        if metadata.confidence < CONFIDENCE_THRESHOLD:
            logger.warning(f"Low confidence ({metadata.confidence}) for image {image_record.id}. Flagging.")
            image_record.status = ImageStatus.FLAGGED_LOW_CONFIDENCE
        else:
            image_record.status = ImageStatus.PROCESSED

        # Upsert or insert tags
        existing_tag = db.query(ImageTagRecord).filter(ImageTagRecord.image_id == image_record.id).first()
        if existing_tag:
            existing_tag.subject = metadata.subject
            existing_tag.category = metadata.category
            existing_tag.attributes = metadata.attributes
            existing_tag.caption = metadata.caption
            existing_tag.confidence = metadata.confidence
        else:
            new_tag = ImageTagRecord(
                image_id=image_record.id,
                subject=metadata.subject,
                category=metadata.category,
                attributes=metadata.attributes,
                caption=metadata.caption,
                confidence=metadata.confidence
            )
            db.add(new_tag)

        db.commit()
        logger.info(f"Successfully processed Image ID {image_record.id} with status {image_record.status.value}.")

    except ValidationError as val_err:
        logger.error(f"Schema validation failed for Image ID {image_record.id}: {val_err}")
        image_record.status = ImageStatus.FAILED
        log_cost_entry(db, VISION_MODEL, "vision_classification", "FAILED_VALIDATION", image_id=image_record.id)
        db.commit()

    except Exception as api_err:
        logger.error(f"Failed API processing for Image ID {image_record.id}: {api_err}")
        image_record.status = ImageStatus.FAILED
        log_cost_entry(db, VISION_MODEL, "vision_classification", "FAILED_API", image_id=image_record.id)
        db.commit()


def run_batch_vision_job():
    """Batch background worker entrypoint: queries all pending images and processes them."""
    db: Session = SessionLocal()
    try:
        pending_images = db.query(ImageRecord).filter(
            ImageRecord.status == ImageStatus.PENDING
        ).all()

        logger.info(f"Starting batch vision processing for {len(pending_images)} pending image(s).")

        for image in pending_images:
            process_single_image(db, image)

        logger.info("Batch vision processing completed.")
    finally:
        db.close()