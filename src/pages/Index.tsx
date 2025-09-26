"use client";

import React, {
  useRef,
  useState,
  useEffect,
  useCallback,
  useMemo,
} from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import CSVVisualizationDashboard from "../utils/CSVVisualizationDashboard";
import type { Message, Chat, MessageContent, ApiResponse } from "@/types";
import { VoiceInput } from "@/components/ui/VoiceInput";
import {
  LineChart,
  Table,
  BookOpenText,
  MessageCircle,
  Waves,
  Search,
  Plus,
  ArrowUp,
  Copy,
  StopCircle,
  ThumbsUp,
  ThumbsDown,
  Pencil,
  Trash,
  MoreHorizontal,
  Sparkles,
  Database,
  TrendingUp,
  Zap,
  Globe,
  BarChart3,
  Activity,
  Languages,
  Image as ImageIcon,
  X,
  Paperclip,
  Settings,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { fetchData } from "@/utils/api";
import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import styles from "./index.module.css";
import FunFacts from "../components/ui/FunFacts";

// Gemini API integration
const GEMINI_API_KEY = "AIzaSyBUM2atvtn4ukAxIm5Z2pm8vRagL8Z8v_I";

const analyzeImageWithGemini = async (
  imageBase64: string,
  userPrompt: string
) => {
  try {
    // System instructions
    const systemPrompt = `
Prompt for ARGO Image Interpretation Mode

System Instruction (always enforced):
You are an Anantha, AI assistant specialized in oceanographic data interpretation, focusing on ARGO floats, CTD casts, BGC parameters, salinity, temperature, and oceanographic visualizations.

Check relevance:
- If the image is related to ARGO data or oceanography (depth-time profiles, salinity/temperature plots, float trajectories, BGC plots), interpret it.
- If not, respond that the image is not relevant.

Output:
- Describe what the visualization represents (variables, dimensions, units, geographic/temporal context).
- Explain trends/patterns scientifically.
- Provide possible oceanographic insights.
- Suggest next-step questions a researcher might ask.

Tone & style:
- Detailed yet intuitive for non-technical audience.
- Use domain terms but explain in plain language.
- Behave like a professor or domain expert, do not act like AI.
`;

    const combinedPrompt = `${systemPrompt}\n\nUser Question: ${userPrompt}`;

    const response = await fetch(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-goog-api-key": GEMINI_API_KEY,
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                { text: combinedPrompt }, // system + user prompt together
                {
                  inlineData: {
                    mimeType: "image/jpeg",
                    data: imageBase64, // base64 WITHOUT prefix
                  },
                },
              ],
            },
          ],
          generationConfig: {
            temperature: 0.7,
            topK: 40,
            topP: 0.95,
            maxOutputTokens: 2048,
          },
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        `Gemini API error: ${response.status} ${await response.text()}`
      );
    }

    const data = await response.json();
    return (
      data.candidates?.[0]?.content?.parts?.find((p) => p.text)?.text || ""
    );
  } catch (error) {
    console.error("Gemini API error:", error);
    throw new Error("Failed to analyze image with AI");
  }
};

function ChatSidebar({
  chats,
  activeChat,
  onChatSelect,
  onNewChat,
  onDeleteChat,
}: {
  chats: Chat[];
  activeChat: string | null;
  onChatSelect: (chatId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
}) {
  return (
    <Sidebar className="border-r border-border/50 bg-[hsl(210_100%_5%)]">
      <SidebarHeader className="bg-[hsl(210_100%_5%)] border-b border-border/30">
        <div className="flex items-center justify-between gap-2 p-4">
          <div className="flex items-center gap-3">
            <div className="relative flex items-center justify-center size-10 rounded-xl bg-primary">
              <Waves className="absolute left-1.5 top-1.5 size-3 text-black" />
              <Database className="absolute right-1.5 bottom-1.5 size-3 text-black" />
            </div>
            <div>
              <div className="text-lg font-bold text-white tracking-tight">
                Anantha
              </div>
              <div className="text-xs text-gray-400">
                Data Intelligence Platform
              </div>
            </div>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-9 text-white hover:bg-[hsl(210_100%_5%)]"
                >
                  <Search className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Search conversations</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </SidebarHeader>

      <SidebarContent className="p-4">
        <Button
          variant="default"
          className="mb-6 w-full bg-primary text-black hover:bg-primary/90 transition-all duration-300 font-semibold shadow-md"
          onClick={onNewChat}
        >
          <Plus className="size-4 mr-2" />
          <span>New Analysis</span>
          <Sparkles className="size-4 ml-2" />
        </Button>

        {chats.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel className="text-xs font-medium text-gray-400 px-2 mb-3">
              Recent Conversations
            </SidebarGroupLabel>
            <SidebarMenu className="space-y-2">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={cn(
                    "group flex items-center gap-2 rounded-lg p-3 transition-all duration-200",
                    activeChat === chat.id
                      ? "bg-[hsl(210_100%_5%)] border border-gray-700"
                      : "hover:bg-[hsl(210_100%_5%)]"
                  )}
                >
                  <SidebarMenuButton
                    onClick={() => onChatSelect(chat.id)}
                    className="flex-1 justify-start p-0 h-auto font-normal text-white"
                  >
                    <div className="flex items-center gap-3 w-full">
                      <div className="size-8 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
                        <MessageCircle className="size-4 text-primary" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate font-medium text-sm text-white">
                          {chat.title}
                        </div>
                        <div className="text-xs text-gray-400">
                          {chat.messages.length} messages
                        </div>
                      </div>
                    </div>
                  </SidebarMenuButton>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-8 opacity-0 group-hover:opacity-100 transition-opacity text-white hover:bg-gray-700"
                      >
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                      align="end"
                      className="bg-[hsl(210_100%_5%)] border-gray-700 text-white"
                    >
                      <DropdownMenuItem
                        onClick={() => onDeleteChat(chat.id)}
                        className="text-white hover:bg-[hsl(210_100%_5%)]"
                      >
                        <Trash className="size-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        )}
      </SidebarContent>
    </Sidebar>
  );
}

function MessageBubble({
  message,
  isLastMessage,
  onEdit,
  onDelete,
  isEditing,
  onSaveEdit,
  editText,
  setEditText,
  onVote,
  votedState,
}: {
  message: Message;
  isLastMessage: boolean;
  onEdit: (messageId: string | null) => void;
  onDelete: (messageId: string) => void;
  isEditing: boolean;
  onSaveEdit: () => void;
  editText: string;
  setEditText: (text: string) => void;
  onVote: (messageId: string, vote: "up" | "down") => void;
  votedState: { [key: string]: "up" | "down" | null };
}) {
  const isAssistant = message.role === "assistant";
  const { toast } = useToast();
  const isUpvoted = votedState[message.id] === "up";
  const isDownvoted = votedState[message.id] === "down";

  const handleCopy = async (content: string | MessageContent) => {
    try {
      let textToCopy = "";
      if (typeof content === "string") {
        textToCopy = content;
      } else {
        // Convert the entire message content to a string for copying
        if (content.type === "table") {
          textToCopy =
            content.explanation +
            "\n\n" +
            content.tableData.map((row) => row.join("\t")).join("\n");
        } else if (content.type === "plot") {
          textToCopy =
            content.explanation +
            "\n\n" +
            JSON.stringify(content.plotData, null, 2);
        } else if (content.type === "theory") {
          textToCopy = content.component + "\n\n" + content.explanation;
        } else if (content.type === "image") {
          textToCopy = content.analysis || "Image analysis";
        } else {
          textToCopy = JSON.stringify(content, null, 2);
        }
      }

      await navigator.clipboard.writeText(textToCopy);
      toast({
        title: "Copied to clipboard",
        description: "Message content has been copied.",
      });
    } catch (err) {
      console.error("Copy failed:", err);
      toast({
        title: "Copy failed",
        description: "Could not copy to clipboard.",
        variant: "destructive",
      });
    }
  };

  const handleVote = (vote: "up" | "down") => {
    onVote(message.id, vote);
    toast({
      title:
        vote === "up"
          ? "Thanks for your feedback!"
          : "Thank you for helping us with this intimation.",

      description:
        vote === "up"
          ? "This positive rating helps us reinforce the chatbot's current response patterns. Your input strengthens the underlying reinforcement learning model, making it more likely to generate similar high-quality answers in future conversations.\n\nEvery response you give matters — it helps make our system smarter and better for you."
          : "This negative rating signals our reinforcement learning system to adjust its weights and reduce the likelihood of generating similar responses again. Over time, your feedback helps fine-tune the model toward more accurate and contextually relevant answers.\n\nEvery response you give matters — it helps make our system smarter and better for you.",
    });
  };

  const renderContent = () => {
    const content = message.content;
    if (typeof content === "string") {
      return (
        <div className="prose prose-slate max-w-none dark:prose-invert">
          <div className="whitespace-pre-wrap text-black break-words">
            {content}
          </div>
        </div>
      );
    }

    if (content && typeof content === "object") {
      // Image content
      if (content.type === "image") {
        return (
          <div className="space-y-4">
            {content.imageUrl && (
              <div className="rounded-lg overflow-hidden border border-gray-700">
                <img
                  src={content.imageUrl}
                  alt="Uploaded image"
                  className="w-full max-w-md h-auto"
                />
              </div>
            )}
            {content.analysis && (
              <div className="bg-[hsl(210_100%_5%)] rounded-lg p-4 border border-gray-700">
                <div
                  className={`
                  prose prose-slate max-w-none dark:prose-invert
                  prose-headings:mt-6 prose-p:my-4 prose-li:my-1
                  whitespace-pre-line ${styles.markdownTable}
                `}
                >
                  <ReactMarkdown remarkPlugins={[remarkBreaks, remarkGfm]}>
                    {content.analysis}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        );
      }

      // Table content
      if (content.type === "table" && content.tableData) {
        return (
          <div className="space-y-6">
            <div className="overflow-x-auto rounded-lg border border-gray-700">
              <table className="w-full border-collapse bg-[hsl(210_100%_5%)] text-white">
                <thead>
                  <tr className="bg-[hsl(210_100%_5%)]">
                    {content.columns?.map((header: string, i: number) => (
                      <th
                        key={i}
                        className="border-b border-gray-700 px-4 py-3 text-left font-medium"
                      >
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {content.tableData.map((row: any, i: number) => (
                    <tr
                      key={i}
                      className="hover:bg-[hsl(210_100%_5%)]/50 transition-colors"
                    >
                      {content.columns?.map((col: string, j: number) => (
                        <td
                          key={j}
                          className="border-b border-gray-700 px-4 py-3 text-white"
                        >
                          {row[col]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {content.explanation && (
              <div className="bg-[hsl(210_100%_5%)] rounded-lg p-4 border border-gray-700">
                <div className="text-sm text-white">{content.explanation}</div>
              </div>
            )}

            {content.csvDownload && (
              <Button
                variant="outline"
                className="border-gray-700 text-white hover:bg-[hsl(210_100%_5%)] transition-all duration-300"
                onClick={() => {
                  window.open(content.csvDownload, "_blank");
                }}
              >
                <Database className="size-4 mr-2" />
                Download CSV
              </Button>
            )}
          </div>
        );
      }

      if (content.type === "plot" && content.csvUrl) {
        return (
          <div className="space-y-4">
            <CSVVisualizationDashboard
              csvFile={content.csvUrl}
              initialPlotType="line"
            />

            <Button
              variant="outline"
              className="border-gray-700 text-white hover:bg-[hsl(210_100%_5%)]"
              onClick={() => window.open(content.csvUrl, "_blank")}
            >
              <Database className="size-4 mr-2" />
              Download Plot Data (CSV)
            </Button>
          </div>
        );
      }

      // Theory content
      if (content.type === "theory") {
        const theoryText = content.message || "No content available.";
        return (
          <div className="bg-[hsl(210_100%_5%)] rounded-lg p-6 border border-gray-700">
            <div
              className={`
          prose prose-slate max-w-none dark:prose-invert
          prose-headings:mt-6 prose-p:my-4 prose-li:my-1
          whitespace-pre-line ${styles.markdownTable}
        `}
            >
              <ReactMarkdown remarkPlugins={[remarkBreaks, remarkGfm]}>
                {theoryText}
              </ReactMarkdown>
            </div>
          </div>
        );
      }
    }

    return (
      <div className="text-muted-foreground p-4 rounded-lg bg-muted/20">
        Unable to render content: {JSON.stringify(content)}
      </div>
    );
  };

  return (
    <div
      className={cn(
        "mx-auto flex w-full max-w-4xl flex-col gap-3 mb-8 px-4 sm:px-6",
        isAssistant ? "items-start" : "items-end"
      )}
    >
      {isAssistant ? (
        <div className="group flex w-full flex-col gap-3 animate-in">
          <div className="flex items-center gap-3">
            <div className="size-8 rounded-lg bg-primary flex items-center justify-center">
              <Activity className="size-4 text-black" />
            </div>
            <div className="text-sm font-medium text-white">Anantha AI</div>
            <Badge
              variant="secondary"
              className="text-xs bg-[hsl(210_100%_5%)] text-white"
            >
              {message.content && typeof message.content === "object"
                ? message.content.type
                : "response"}
            </Badge>
          </div>

          <div className="ml-11">{renderContent()}</div>

          <TooltipProvider>
            <div
              className={cn(
                "ml-8 flex gap-1 opacity-0 transition-opacity duration-200 group-hover:opacity-100",
                isLastMessage && "opacity-100"
              )}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8 rounded-full text-white hover:bg-[hsl(210_100%_5%)]"
                    onClick={() => handleCopy(message.content)}
                  >
                    <Copy className="size-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Copy response</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={isUpvoted ? "default" : "ghost"}
                    size="icon"
                    className={cn(
                      "size-8 rounded-full text-black",
                      isUpvoted
                        ? "bg-green-500 hover:bg-green-600"
                        : "hover:bg-[hsl(210_100%_5%)] text-white"
                    )}
                    onClick={() => handleVote("up")}
                  >
                    <ThumbsUp className="size-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Helpful</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant={isDownvoted ? "default" : "ghost"}
                    size="icon"
                    className={cn(
                      "size-8 rounded-full text-black",
                      isDownvoted
                        ? "bg-red-500 hover:bg-red-600"
                        : "hover:bg-[hsl(210_100%_5%)] text-white"
                    )}
                    onClick={() => handleVote("down")}
                  >
                    <ThumbsDown className="size-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Not helpful</TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        </div>
      ) : (
        <div className="group flex flex-col items-end gap-2">
          {isEditing ? (
            <div className="max-w-[100%] sm:max-w-[100%] space-y-3">
              <Textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="min-h-[100px] bg-[hsl(210_100%_5%)] border-gray-700 text-white resize-none"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={onSaveEdit}
                  className="bg-primary text-black hover:bg-primary/90 font-medium"
                >
                  Save & Regenerate
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onEdit(null)}
                  className="text-white border-gray-700 hover:bg-[hsl(210_100%_5%)]"
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="bg-primary text-black rounded-2xl px-5 py-3 max-w-[85%] sm:max-w-[%] break-words space-y-3">
              {/* Show uploaded image if it exists */}
              {message.uploadedImage && (
                <div className="rounded-lg overflow-hidden">
                  <img
                    src={message.uploadedImage}
                    alt="User uploaded"
                    className="w-full max-w-xs h-auto"
                  />
                </div>
              )}
              <div className="whitespace-pre-wrap font-medium">
                {typeof message.content === "string"
                  ? message.content
                  : JSON.stringify(message.content)}
              </div>
            </div>
          )}

          <TooltipProvider>
            <div className="flex gap-1 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8 rounded-full text-white hover:bg-[hsl(210_100%_5%)]"
                    onClick={() => onEdit(message.id)}
                  >
                    <Pencil className="size-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Edit message</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-8 rounded-full text-white hover:bg-[hsl(210_100%_5%)]"
                    onClick={() => onDelete(message.id)}
                  >
                    <Trash className="size-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Delete message</TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        </div>
      )}
    </div>
  );
}

function ChatContent({
  messages,
  setMessages,
  chatTitle,
}: {
  messages: Message[];
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void;
  chatTitle: string;
}) {
  const [prompt, setPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [editingMessage, setEditingMessage] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [votedMessages, setVotedMessages] = useState<{
    [key: string]: "up" | "down";
  }>({});
  const [selectedLanguage, setSelectedLanguage] = useState("english");
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("Plot");

  // Settings modal state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [explanationLevel, setExplanationLevel] = useState(5);
  const [awarenessLevel, setAwarenessLevel] = useState(5);
  const [objectives, setObjectives] = useState({
    objective1: false,
    objective2: false,
    objective3: false,
  });
  const [featureWishlist, setFeatureWishlist] = useState("");
  const [starRating, setStarRating] = useState(0);
  const [isDarkTheme, setIsDarkTheme] = useState(true);
  const modalRef = useRef(null);

  // Close modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        setIsSettingsOpen(false);
      }
    };

    if (isSettingsOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isSettingsOpen]);

  const handleObjectiveChange = (objective) => {
    setObjectives((prev) => ({
      ...prev,
      [objective]: !prev[objective],
    }));
  };

  const handleApplyPreferences = () => {
    console.log("Settings applied:", {
      explanationLevel,
      awarenessLevel,
      objectives,
      featureWishlist,
      starRating,
      isDarkTheme,
    });
    setIsSettingsOpen(false);
    toast({
      title: "Preferences Applied",
      description: "Your settings have been saved successfully.",
    });
  };

  const handleInput = (e) => {
    e.target.style.height = "auto";
    e.target.style.height = e.target.scrollHeight + "px";
    setPrompt(e.target.value);
  };

  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);

  const handleVoiceTranscript = (transcript: string) => {
    setVoiceTranscript(transcript);
    if (isVoiceActive) {
      setPrompt(transcript);
      // Auto-resize the textarea
      setTimeout(() => {
        const textarea = document.querySelector('textarea');
        if (textarea) {
          textarea.style.height = "auto";
          textarea.style.height = textarea.scrollHeight + "px";
        }
      }, 0);
    }
  };

  const handleVoiceStart = () => {
    setIsVoiceActive(true);
    setVoiceTranscript('');
    toast({
      title: "Voice Recording Started",
      description: "Speak now... Click the mic again to stop.",
    });
  };

  const handleVoiceStop = () => {
    setIsVoiceActive(false);
    // Keep the final transcript in the prompt
    if (voiceTranscript.trim()) {
      setPrompt(voiceTranscript.trim());
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast({
        title: "Invalid file type",
        description: "Please select an image file.",
        variant: "destructive",
      });
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      // 10MB limit
      toast({
        title: "File too large",
        description: "Please select an image smaller than 10MB.",
        variant: "destructive",
      });
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setImagePreview(result);
      setUploadedImage(result);
    };
    reader.readAsDataURL(file);
  };

  const removeImage = () => {
    setUploadedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const generateResponse = async (
    userPrompt: string,
    activeTab: string,
    language: string,
    imageData?: string
  ): Promise<Message> => {
    try {
      // If there's an image, use Gemini API for image analysis
      if (imageData) {
        const base64Image = imageData.split(",")[1]; // Remove data:image/jpeg;base64, prefix
        const analysis = await analyzeImageWithGemini(base64Image, userPrompt);

        return {
          id: `${Date.now()}-${Math.random()}`,
          role: "assistant",
          content: {
            type: "image",
            imageUrl: imageData,
            analysis: analysis,
          },
        };
      }

      // Original logic for non-image messages
      console.log("sending to backend", {
        tab: activeTab.toLowerCase(),
        query: userPrompt,
        language,
        imageData,
      });

      const response = await fetchData(
        userPrompt,
        activeTab.toLowerCase(),
        language,
        imageData
      );

      let content: MessageContent;
      console.log("response from backend:", response);
      console.log("response.type:", response.type);

      switch (response.type) {
        case "table":
          content = {
            type: "table",
            tableData: response.raw_data || [],
            columns: response.columns || [],
            explanation: response.message || "No explanation available.",
            csvDownload: response.csv_url || "",
          };
          break;

        case "plot":
          content = {
            type: "plot",
            csvUrl: response.csv_url || "",
            explanation: response.message || "Data prepared for plotting.",
            plotType: "line",
          };
          break;

        case "theory":
          content = {
            type: "theory",
            message: response.message || "No theory content available.",
          };
          break;

        default:
          content = {
            type: "theory",
            message: "Invalid tab selection.",
          };
      }

      return {
        id: `${Date.now()}-${Math.random()}`,
        role: "assistant",
        content,
      };
    } catch (error: any) {
      if (error.name === "AbortError") {
        throw new Error("Request was aborted");
      }
      console.error("Error generating response:", error);
      throw error;
    }
  };

  const handleSubmit = async (submitPrompt?: string) => {
    const finalPrompt = submitPrompt || prompt.trim();
    if ((!finalPrompt && !uploadedImage) || isLoading) return;

    if (!submitPrompt) {
      setPrompt("");
    }

    setIsLoading(true);

    abortControllerRef.current = new AbortController();

    const newUserMessage: Message = {
      id: `${Date.now()}-${Math.random()}`,
      role: "user",
      content: finalPrompt || "Analyze this image",
      uploadedImage: uploadedImage,
    };

    setMessages((prev) => [...prev, newUserMessage]);

    try {
      const response = await generateResponse(
        finalPrompt,
        activeTab,
        selectedLanguage,
        uploadedImage
      );

      setMessages((prev) => [...prev, response]);
    } catch (error: any) {
      console.error("Error generating response:", error);
      if (error.name !== "AbortError") {
        toast({
          title: "Analysis Failed",
          description: `Unable to process your request: ${error.message}`,
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
      // Clear the uploaded image after sending
      setUploadedImage(null);
      setImagePreview(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsLoading(false);
  };

  const handleEditMessage = (messageId: string | null) => {
    if (messageId === null) {
      setEditingMessage(null);
      setEditText("");
      return;
    }

    const message = messages.find((m) => m.id === messageId);
    if (message && typeof message.content === "string") {
      setEditingMessage(messageId);
      setEditText(message.content);
    }
  };

  const handleSaveEdit = () => {
    // Update the message
    setMessages((prev) =>
      prev.map((msg) =>
        msg.id === editingMessage ? { ...msg, content: editText } : msg
      )
    );

    // Generate a new response for the edited message
    handleSubmit(editText);

    setEditingMessage(null);
    setEditText("");
  };

  const handleDeleteMessage = (messageId: string) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== messageId));
    toast({
      title: "Message deleted",
      description: "The message has been removed from the conversation.",
    });
  };

  const handleVote = (messageId: string, vote: "up" | "down") => {
    setVotedMessages((prev) => ({ ...prev, [messageId]: vote }));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const analysisTypes = [
    {
      id: "Plot",
      icon: BarChart3,
      label: "Visualizations",
      description: "Generate interactive charts and graphs",
    },
    {
      id: "Table",
      icon: Table,
      label: "Data Tables",
      description: "Structure and analyze tabular data",
    },
    {
      id: "Theory",
      icon: BookOpenText,
      label: "Theory & Insights",
      description: "Get detailed explanations and analysis",
    },
  ];

  const languages = [
    { value: "english", label: "English" },
    { value: "hindi", label: "Hindi" },
    { value: "tamil", label: "Tamil" },
    { value: "telugu", label: "Telugu" },
    { value: "bengali", label: "Bengali" },
    { value: "marathi", label: "Marathi" },
    { value: "punjabi", label: "Punjabi" },
    { value: "afrikaans", label: "Afrikaans" },
    { value: "amharic", label: "Amharic" },
    { value: "assamese", label: "Assamese" },
    { value: "azerbaijani", label: "Azerbaijani" },
    { value: "belarusian", label: "Belarusian" },
    { value: "bosnian", label: "Bosnian" },
    { value: "catalan", label: "Catalan" },
    { value: "cebuano", label: "Cebuano" },
    { value: "corsican", label: "Corsican" },
    { value: "welsh", label: "Welsh" },
    { value: "dhivehi", label: "Dhivehi" },
    { value: "esperanto", label: "Esperanto" },
    { value: "basque", label: "Basque" },
    { value: "persian", label: "Persian / Farsi" },
    { value: "filipino", label: "Filipino (Tagalog)" },
    { value: "frisian", label: "Frisian" },
    { value: "irish", label: "Irish" },
    { value: "scots_gaelic", label: "Scots Gaelic" },
    { value: "galician", label: "Galician" },
    { value: "gujarati", label: "Gujarati" },
    { value: "hausa", label: "Hausa" },
    { value: "hawaiian", label: "Hawaiian" },
    { value: "hmong", label: "Hmong" },
    { value: "haitian_creole", label: "Haitian Creole" },
    { value: "armenian", label: "Armenian" },
    { value: "igbo", label: "Igbo" },
    { value: "icelandic", label: "Icelandic" },
    { value: "javanese", label: "Javanese" },
    { value: "georgian", label: "Georgian" },
    { value: "kazakh", label: "Kazakh" },
    { value: "khmer", label: "Khmer" },
    { value: "kannada", label: "Kannada" },
    { value: "kri", label: "Krio" },
    { value: "kurdish", label: "Kurdish" },
    { value: "kyrgyz", label: "Kyrgyz" },
    { value: "latin", label: "Latin" },
    { value: "luxembourgish", label: "Luxembourgish" },
    { value: "lao", label: "Lao" },
    { value: "malagasy", label: "Malagasy" },
    { value: "maori", label: "Maori" },
    { value: "macedonian", label: "Macedonian" },
    { value: "malayalam", label: "Malayalam" },
    { value: "mongolian", label: "Mongolian" },
    { value: "manipuri", label: "Meiteilon / Manipuri" },
    { value: "malay", label: "Malay" },
    { value: "maltese", label: "Maltese" },
    { value: "burmese", label: "Burmese (Myanmar)" },
    { value: "nepali", label: "Nepali" },
    { value: "nyanja", label: "Nyanja / Chichewa" },
    { value: "odia", label: "Odia (Oriya)" },
    { value: "pashto", label: "Pashto" },
    { value: "sindhi", label: "Sindhi" },
    { value: "sinhala", label: "Sinhala / Sinhalese" },
    { value: "samoan", label: "Samoan" },
    { value: "shona", label: "Shona" },
    { value: "somali", label: "Somali" },
    { value: "albanian", label: "Albanian" },
    { value: "sesotho", label: "Sesotho" },
    { value: "sundanese", label: "Sundanese" },
    { value: "tajik", label: "Tajik" },
    { value: "urdu", label: "Urdu" },
    { value: "uyghur", label: "Uyghur" },
    { value: "uzbek", label: "Uzbek" },
    { value: "xhosa", label: "Xhosa" },
    { value: "yiddish", label: "Yiddish" },
    { value: "yoruba", label: "Yoruba" },
    { value: "zulu", label: "Zulu" },
  ];

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-[hsl(210_100%_5%)]">
      <header className="bg-[hsl(210_100%_5%)] backdrop-blur-md z-10 flex h-16 w-full shrink-0 items-center gap-4 border-b border-gray-700 px-6">
        <SidebarTrigger className="-ml-1 text-white hover:bg-[hsl(210_100%_5%)] transition-all duration-300" />
        <div className="flex items-center gap-3 flex-1">
          <div className="text-white font-medium">{chatTitle}</div>
          <Badge
            variant="secondary"
            className="text-xs bg-[hsl(210_100%_5%)] text-white"
          >
            {activeTab} Mode
          </Badge>
        </div>

        {/* Settings Icon */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setIsSettingsOpen(true)}
                className="text-white hover:bg-gray-700 p-2 rounded-lg transition-colors duration-200"
                aria-label="Open settings"
              >
                <Settings className="w-5 h-5" />
              </button>
            </TooltipTrigger>
            <TooltipContent>Settings</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </header>

      {/* Settings Modal Overlay */}
      {isSettingsOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div
            ref={modalRef}
            className="bg-gray-900 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">
                  <i className="fas fa-sliders-h mr-2"></i> Chatbot Preferences
                </h2>
                <button
                  onClick={() => setIsSettingsOpen(false)}
                  className="text-gray-400 hover:text-white transition-colors duration-200"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Profile Section */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  What best describes your role?
                </label>
                <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option>Student</option>
                  <option>Working Professional</option>
                  <option>Research Expert</option>
                  <option>Working in ARGO/Oceanography</option>
                  <option>Domain Expert/Scientist</option>
                </select>
              </div>

              {/* Explanation Preferences */}
              <div className="space-y-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    On a scale of 1-10, what level of explanations do you need?
                    ({explanationLevel})
                  </label>
                  <div className="flex justify-between text-gray-400 text-xs mb-1">
                    <span>Simple (1)</span>
                    <span>Detailed (10)</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={explanationLevel}
                    onChange={(e) =>
                      setExplanationLevel(parseInt(e.target.value))
                    }
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    On a scale of 1-10, how familiar are you with ARGO data and
                    oceanography? ({awarenessLevel})
                  </label>
                  <div className="flex justify-between text-gray-400 text-xs mb-1">
                    <span>Novice (1)</span>
                    <span>Expert (10)</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={awarenessLevel}
                    onChange={(e) =>
                      setAwarenessLevel(parseInt(e.target.value))
                    }
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
              </div>

              {/* Objectives Checkboxes */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  What are your main objectives with this application? (Select
                  all that apply)
                </label>
                <div className="space-y-2">
                  {[
                    "Advanced Reasoning",
                    "Theoretical Discussions",
                    "Visualizations",
                    "Data Fetching",
                    "Data Download",
                    "Other Features",
                  ].map((obj, idx) => (
                    <label key={idx} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={objectives[`objective${idx + 1}`]}
                        onChange={() =>
                          handleObjectiveChange(`objective${idx + 1}`)
                        }
                        className="w-4 h-4 text-blue-600 bg-gray-800 border-gray-700 rounded focus:ring-blue-500"
                      />
                      <span className="text-gray-300">{obj}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Feature Wishlist */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  What feature would you like to see added to this application?
                </label>
                <textarea
                  value={featureWishlist}
                  onChange={(e) => setFeatureWishlist(e.target.value)}
                  className="w-full h-24 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="Tell us about your ideal feature..."
                />
              </div>

              {/* Star Rating */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  How would you rate your experience with our chatbot so far?
                </label>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setStarRating(star)}
                      className="text-2xl focus:outline-none"
                    >
                      {star <= starRating ? (
                        <span className="text-yellow-400">★</span>
                      ) : (
                        <span className="text-gray-400">☆</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Apply Button */}
              <div className="flex justify-end pt-4 border-t border-gray-700">
                <button
                  onClick={handleApplyPreferences}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors duration-200 font-medium"
                >
                  Apply Preferences
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <ScrollArea ref={chatContainerRef} className="flex-1 px-4">
        <div className="py-4">
          {messages.length === 0 && (
            <div className="mx-auto max-w-4xl text-center pt-16 pb-16">
              <div className="relative flex items-center justify-center size-20 rounded-2xl bg-primary mx-auto mb-6">
                <Waves className="absolute left-3 top-3 size-5 text-black" />
                <Sparkles className="absolute right-3 bottom-3 size-5 text-black" />
              </div>
              <h2 className="text-3xl font-bold mb-3 text-white">
                Welcome to Anantha
              </h2>
              <p className="text-base text-gray-400 mb-8 max-w-2xl mx-auto">
                Your intelligent data analysis companion. Explore ocean data,
                generate visualizations, and uncover insights with AI-powered
                analytics.
              </p>
              <FunFacts />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
                {analysisTypes.map((type) => (
                  <Card
                    key={type.id}
                    className="p-4 hover:border-primary transition-all duration-300 cursor-pointer bg-[hsl(210_100%_5%)] border-gray-700"
                  >
                    <div className="text-center space-y-3">
                      <div className="size-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto">
                        <type.icon className="size-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-medium text-white">{type.label}</h3>
                        <p className="text-sm text-gray-400">
                          {type.description}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble
              key={message.id}
              message={message}
              isLastMessage={index === messages.length - 1}
              onEdit={handleEditMessage}
              onDelete={handleDeleteMessage}
              isEditing={editingMessage === message.id}
              onSaveEdit={handleSaveEdit}
              editText={editText}
              setEditText={setEditText}
              onVote={handleVote}
              votedState={votedMessages}
            />
          ))}

          {isLoading && (
            <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 mb-8 px-4 sm:px-6 items-start">
              <div className="flex items-center gap-3">
                <div className="size-8 rounded-lg bg-primary flex items-center justify-center">
                  <Activity className="size-4 text-black" />
                </div>
                <div className="flex items-center gap-2">
                  <div className="animate-spin size-4 border-2 border-primary border-t-transparent rounded-full"></div>
                  <span className="text-gray-400 font-medium">
                    {uploadedImage
                      ? "Analyzing image..."
                      : "Analyzing your data..."}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleStopGeneration}
                    className="ml-3 text-white hover:bg-[hsl(210_100%_5%)]"
                  >
                    <StopCircle className="size-4 mr-1" />
                    Stop
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="bg-[hsl(210_100%_5%)] backdrop-blur-md z-10 shrink-0 p-4 md:p-6 border-gray-700">
        <div className="mx-auto max-w-4xl">
          <Card className="relative border border-gray-700 p-0 bg-[hsl(210_100%_5%)]">
            <CardContent className="p-0">
              <div className="flex flex-col">
                {/* Image Preview */}
                {imagePreview && (
                  <div className="p-4 border-b border-gray-700">
                    <div className="relative inline-block">
                      <img
                        src={imagePreview}
                        alt="Upload preview"
                        className="max-w-xs max-h-32 rounded-lg border border-gray-600"
                      />
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute -top-2 -right-2 size-6 rounded-full bg-red-500 text-white hover:bg-red-600"
                        onClick={removeImage}
                      >
                        <X className="size-3" />
                      </Button>
                    </div>
                  </div>
                )}

                <Textarea
                  placeholder={
                    imagePreview
                      ? "Describe what you want to know about this image..."
                      : "Analyze ocean temperature patterns..."
                  }
                  value={prompt}
                  onInput={handleInput}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                  style={{ minHeight: "60px" }}
                  className="
                    border-0 
                    resize-none 
                    overflow-hidden
                    pt-4 px-4 text-base
                    bg-[hsl(210_100%_5%)] text-white placeholder:text-gray-500
                  "
                />

                <div className="mt-4 flex w-full items-center justify-between gap-3 px-4 pb-4 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* Image upload button */}
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="outline"
                            size="icon"
                            className="rounded-xl text-white border-gray-700 hover:bg-gray-700 transition-all duration-300 mb-2"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isLoading}
                          >
                            <ImageIcon className="size-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Upload image</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="hidden"
                    />

                    {/* Voice input button */}
                    <VoiceInput
                      onTranscript={handleVoiceTranscript}
                      onStart={handleVoiceStart}
                      onStop={handleVoiceStop}
                      className="rounded-xl border border-gray-700 hover:bg-gray-700 transition-all duration-300 mb-2"
                      disabled={isLoading}
                      language={selectedLanguage === 'english' ? 'en-US' : 
                               selectedLanguage === 'spanish' ? 'es-ES' :
                               selectedLanguage === 'french' ? 'fr-FR' :
                               selectedLanguage === 'german' ? 'de-DE' :
                               selectedLanguage === 'italian' ? 'it-IT' :
                               selectedLanguage === 'portuguese' ? 'pt-PT' :
                               selectedLanguage === 'russian' ? 'ru-RU' :
                               selectedLanguage === 'japanese' ? 'ja-JP' :
                               selectedLanguage === 'korean' ? 'ko-KR' :
                               selectedLanguage === 'chinese' ? 'zh-CN' :
                               selectedLanguage === 'arabic' ? 'ar-SA' :
                               selectedLanguage === 'hindi' ? 'hi-IN' : 'en-US'}
                    />

                    <TooltipProvider>
                      {analysisTypes.map((type) => (
                        <Tooltip key={type.id}>
                          <TooltipTrigger asChild>
                            <Button
                              variant={
                                activeTab === type.id ? "default" : "outline"
                              }
                              className={cn(
                                "rounded-xl transition-all duration-300 mb-2 font-medium",
                                activeTab === type.id
                                  ? "bg-primary text-black"
                                  : "text-white border-gray-700 hover:bg-gray-700"
                              )}
                              disabled={isLoading}
                              onClick={() => setActiveTab(type.id)}
                            >
                              <type.icon size={16} className="mr-2" />
                              <span className="hidden sm:inline">
                                {type.label}
                              </span>
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent className="bg-[hsl(210_100%_5%)] text-white border-gray-700">
                            <div className="text-center">
                              <div className="font-medium">{type.label}</div>
                              <div className="text-xs text-gray-400">
                                {type.description}
                              </div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      ))}
                    </TooltipProvider>

                    <Select
                      value={selectedLanguage}
                      onValueChange={setSelectedLanguage}
                    >
                      <SelectTrigger className="w-[120px] bg-primary border-primary text-black mb-2 font-medium">
                        <Globe className="size-4 mr-2" />
                        <SelectValue placeholder="Language" />
                      </SelectTrigger>
                      <SelectContent className="bg-[hsl(210_100%_5%)] border-gray-700 text-white">
                        {languages.map((lang) => (
                          <SelectItem
                            key={lang.value}
                            value={lang.value}
                            className="focus:bg-[hsl(210_100%_5%)]"
                          >
                            {lang.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center gap-2">
                    <TooltipProvider>
                      {isLoading ? (
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={handleStopGeneration}
                          className="size-10 rounded-xl text-white border-gray-700 hover:bg-gray-700 mb-2"
                        >
                          <StopCircle size={18} />
                        </Button>
                      ) : (
                        <Button
                          size="icon"
                          disabled={
                            (!prompt.trim() && !uploadedImage) || isLoading
                          }
                          onClick={() => handleSubmit()}
                          className="size-10 rounded-xl bg-primary text-black hover:bg-primary/90 transition-all duration-300 mb-2"
                        >
                          <ArrowUp size={18} />
                        </Button>
                      )}
                    </TooltipProvider>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Custom slider styles */}
      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
        }

        .slider::-moz-range-thumb {
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
        }
      `}</style>
    </main>
  );
}

const Index = () => {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [chatCounter, setChatCounter] = useState(1);

  const createNewChat = useCallback(() => {
    const newChatId = Date.now().toString();
    const newChat: Chat = {
      id: newChatId,
      title: `Analysis Session ${chatCounter}`,
      messages: [],
      createdAt: new Date(),
    };

    setChats((prev) => {
      if (prev.some((c) => c.title === newChat.title)) return prev;
      return [newChat, ...prev];
    });
    setActiveChat(newChatId);
    setChatCounter((prev) => prev + 1);
  }, [chatCounter]);

  const deleteChat = useCallback(
    (chatId: string) => {
      setChats((prev) => prev.filter((c) => c.id !== chatId));
      if (activeChat === chatId) {
        const remainingChats = chats.filter((c) => c.id !== chatId);
        setActiveChat(remainingChats.length > 0 ? remainingChats[0].id : null);
      }
    },
    [activeChat, chats]
  );

  const updateChatTitle = useCallback(
    (chatId: string, messages: Message[]) => {
      const chat = chats.find((c) => c.id === chatId);
      if (chat && chat.title.startsWith("Analysis Session")) {
        const firstUserMessage = messages.find((m) => m.role === "user");
        if (firstUserMessage && typeof firstUserMessage.content === "string") {
          const title =
            firstUserMessage.content.slice(0, 40) +
            (firstUserMessage.content.length > 40 ? "..." : "");
          setChats((prev) =>
            prev.map((c) => (c.id === chatId ? { ...c, title } : c))
          );
        }
      }
    },
    [chats]
  );

  const selectChat = useCallback((chatId: string) => {
    setActiveChat(chatId);
  }, []);

  const currentChat = chats.find((chat) => chat.id === activeChat);

  useEffect(() => {
    if (chats.length === 0) {
      createNewChat();
    }
  }, [chats.length, createNewChat]);

  // Auto-update chat titles
  useEffect(() => {
    if (currentChat && currentChat.messages.length > 0) {
      updateChatTitle(currentChat.id, currentChat.messages);
    }
  }, [currentChat, updateChatTitle]);

  return (
    <div className="dark min-h-screen bg-[hsl(210_100%_5%)]">
      <TooltipProvider>
        <SidebarProvider>
          <ChatSidebar
            chats={chats}
            activeChat={activeChat}
            onChatSelect={selectChat}
            onNewChat={createNewChat}
            onDeleteChat={deleteChat}
          />
          <SidebarInset>
            {currentChat ? (
              <ChatContent
                messages={currentChat.messages}
                setMessages={(update) => {
                  setChats((prevChats) =>
                    prevChats.map((chat) => {
                      if (chat.id === currentChat.id) {
                        const newMessages =
                          typeof update === "function"
                            ? update(chat.messages)
                            : update;
                        return { ...chat, messages: newMessages };
                      }
                      return chat;
                    })
                  );
                }}
                chatTitle={currentChat.title}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center space-y-4">
                  <div className="size-16 rounded-2xl bg-primary mx-auto flex items-center justify-center">
                    <Sparkles className="size-8 text-black" />
                  </div>
                  <div className="text-xl font-medium text-gray-400">
                    Create a new analysis session to get started
                  </div>
                </div>
              </div>
            )}
          </SidebarInset>
        </SidebarProvider>
      </TooltipProvider>
    </div>
  );
};

export default Index;
