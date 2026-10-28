import OpenAI from "openai";

const client = new OpenAI({
  baseURL: process.env.ISMS_BASE_URL ?? "https://api.ismscopilot.com/v1",
  apiKey: process.env.ISMS_API_KEY,
});

// `ismscopilot` is the API's extension field. The OpenAI types do not know it,
// so the request object is widened before it is sent; the SDK passes it through.
const request = {
  model: process.env.ISMS_MODEL ?? "isms-fast",
  messages: [
    {
      role: "user" as const,
      content:
        "Which ISO/IEC 27001:2022 Annex A control covers acceptable use of information and other assets? Answer in one line.",
    },
  ],
  ismscopilot: { frameworks: ["ISO_27001"] },
} as OpenAI.Chat.ChatCompletionCreateParamsNonStreaming;

const { data, response } = await client.chat.completions.create(request).withResponse();

console.log(data.choices[0].message.content);
console.log("x-isms-frameworks:", response.headers.get("x-isms-frameworks"));
