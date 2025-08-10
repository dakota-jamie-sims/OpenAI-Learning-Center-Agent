Vision fine-tuning
==================

Fine-tune models for better image understanding.

Vision fine-tuning uses image inputs for [supervised fine-tuning](/docs/guides/supervised-fine-tuning) to improve the model's understanding of image inputs. This guide will take you through this subset of SFT, and outline some of the important considerations for fine-tuning with image inputs.

  

||
|Provide image inputs for supervised fine-tuning to improve the model's understanding of image inputs.|Image classificationCorrecting failures in instruction following for complex prompts|gpt-4o-2024-08-06|

Data format
-----------

Just as you can [send one or many image inputs and create model responses based on them](/docs/guides/vision), you can include those same message types within your JSONL training data files. Images can be provided either as HTTP URLs or data URLs containing Base64-encoded images.

Here's an example of an image message on a line of your JSONL file. Below, the JSON object is expanded for readability, but typically this JSON would appear on a single line in your data file:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an assistant that identifies uncommon cheeses."
    },
    {
      "role": "user",
      "content": "What is this cheese?"
    },
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "https://upload.wikimedia.org/wikipedia/commons/3/36/Danbo_Cheese.jpg"
          }
        }
      ]
    },
    {
      "role": "assistant",
      "content": "Danbo"
    }
  ]
}
```

Uploading training data for vision fine-tuning follows the [same process described here](/docs/guides/supervised-fine-tuning).

Image data requirements
-----------------------

#### Size

*   Your training file can contain a maximum of 50,000 examples that contain images (not including text examples).
*   Each example can have at most 10 images.
*   Each image can be at most 10 MB.

#### Format

*   Images must be JPEG, PNG, or WEBP format.
*   Your images must be in the RGB or RGBA image mode.
*   You cannot include images as output from messages with the `assistant` role.

#### Content moderation policy

We scan your images before training to ensure that they comply with our usage policy. This may introduce latency in file validation before fine-tuning begins.

Images containing the following will be excluded from your dataset and not used for training:

*   People
*   Faces
*   Children
*   CAPTCHAs

#### What to do if your images get skipped

Your images can get skipped during training for the following reasons:

*   **contains CAPTCHAs**, **contains people**, **contains faces**, **contains children**
    *   Remove the image. For now, we cannot fine-tune models with images containing these entities.
*   **inaccessible URL**
    *   Ensure that the image URL is publicly accessible.
*   **image too large**
    *   Please ensure that your images fall within our [dataset size limits](/docs/guides/vision-fine-tuning#size).
*   **invalid image format**
    *   Please ensure that your images fall within our [dataset format](/docs/guides/vision-fine-tuning#format).

Best practices
--------------

#### Reducing training cost

If you set the `detail` parameter for an image to `low`, the image is resized to 512 by 512 pixels and is only represented by 85 tokens regardless of its size. This will reduce the cost of training. [See here for more information.](/docs/guides/vision#low-or-high-fidelity-image-understanding)

```json
{
  "type": "image_url",
  "image_url": {
    "url": "https://upload.wikimedia.org/wikipedia/commons/3/36/Danbo_Cheese.jpg",
    "detail": "low"
  }
}
```

#### Control image quality

To control the fidelity of image understanding, set the `detail` parameter of `image_url` to `low`, `high`, or `auto` for each image. This will also affect the number of tokens per image that the model sees during training time, and will affect the cost of training. [See here for more information](/docs/guides/vision#low-or-high-fidelity-image-understanding).

Safety checks
-------------

Before launching in production, review and follow the following safety information.

How we assess for safety

Once a fine-tuning job is completed, we assess the resulting model’s behavior across 13 distinct safety categories. Each category represents a critical area where AI outputs could potentially cause harm if not properly controlled.

|Name|Description|
|---|---|
|advice|Advice or guidance that violates our policies.|
|harassment/threatening|Harassment content that also includes violence or serious harm towards any target.|
|hate|Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g., chess players) is harassment.|
|hate/threatening|Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.|
|highly-sensitive|Highly sensitive data that violates our policies.|
|illicit|Content that gives advice or instruction on how to commit illicit acts. A phrase like "how to shoplift" would fit this category.|
|propaganda|Praise or assistance for ideology that violates our policies.|
|self-harm/instructions|Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts.|
|self-harm/intent|Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders.|
|sensitive|Sensitive data that violates our policies.|
|sexual/minors|Sexual content that includes an individual who is under 18 years old.|
|sexual|Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).|
|violence|Content that depicts death, violence, or physical injury.|

Each category has a predefined pass threshold; if too many evaluated examples in a given category fail, OpenAI blocks the fine-tuned model from deployment. If your fine-tuned model does not pass the safety checks, OpenAI sends a message in the fine-tuning job explaining which categories don't meet the required thresholds. You can view the results in the moderation checks section of the fine-tuning job.

How to pass safety checks

In addition to reviewing any failed safety checks in the fine-tuning job object, you can retrieve details about which categories failed by querying the [fine-tuning API events endpoint](https://platform.openai.com/docs/api-reference/fine-tuning/list-events). Look for events of type `moderation_checks` for details about category results and enforcement. This information can help you narrow down which categories to target for retraining and improvement. The [model spec](https://cdn.openai.com/spec/model-spec-2024-05-08.html#overview) has rules and examples that can help identify areas for additional training data.

While these evaluations cover a broad range of safety categories, conduct your own evaluations of the fine-tuned model to ensure it's appropriate for your use case.

Next steps
----------

Now that you know the basics of vision fine-tuning, explore these other methods as well.

[

Supervised fine-tuning

Fine-tune a model by providing correct outputs for sample inputs.

](/docs/guides/supervised-fine-tuning)[

Direct preference optimization

Fine-tune a model using direct preference optimization (DPO).

](/docs/guides/direct-preference-optimization)[

Reinforcement fine-tuning

Fine-tune a reasoning model by grading its outputs.

](/docs/guides/reinforcement-fine-tuning)

Was this page useful?