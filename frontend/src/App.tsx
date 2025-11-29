import { createSignal, createEffect, For, Show } from 'solid-js';
import { SolidMarkdown } from 'solid-markdown';

type Message = {
    role: 'user' | 'assistant';
    content: string;
};

function App() {
    const [messages, setMessages] = createSignal<Message[]>([]);
    const [input, setInput] = createSignal('');
    const [isLoading, setIsLoading] = createSignal(false);
    let messagesEndRef: HTMLDivElement | undefined;

    const scrollToBottom = () => {
        messagesEndRef?.scrollIntoView({ behavior: 'smooth' });
    };

    createEffect(() => {
        messages();
        scrollToBottom();
    });

    const handleSubmit = async (e: Event) => {
        e.preventDefault();
        if (!input().trim() || isLoading()) return;

        const userMsg = input();
        setInput('');
        setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        // Create a placeholder for assistant response
        setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: messages().slice(0, -1).map(m => ({ role: m.role, content: m.content })) // Send history excluding the empty assistant msg
                }),
            });

            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let assistantMessage = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const content = line.slice(6);
                        assistantMessage += content;

                        // Update the last message
                        setMessages((prev) => {
                            const newMessages = [...prev];
                            newMessages[newMessages.length - 1] = { role: 'assistant', content: assistantMessage };
                            return newMessages;
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            setMessages((prev) => [...prev, { role: 'assistant', content: 'Error: Failed to get response.' }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div class="flex flex-col h-screen max-w-4xl mx-auto p-4">
            <header class="mb-4 text-center">
                <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
                    AI Agent Chat
                </h1>
                <p class="text-gray-400 text-sm">Powered by Grok-4-fast</p>
            </header>

            <div class="flex-1 overflow-y-auto bg-gray-800/50 backdrop-blur-md rounded-xl p-4 shadow-2xl border border-gray-700 mb-4">
                <For each={messages()}>
                    {(msg) => (
                        <div class={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div
                                class={`max-w-[80%] rounded-2xl px-4 py-2 ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-br-none'
                                        : 'bg-gray-700 text-gray-100 rounded-bl-none'
                                    }`}
                            >
                                <Show when={msg.role === 'assistant'} fallback={<p>{msg.content}</p>}>
                                    <div class="prose prose-invert max-w-none text-sm">
                                        <SolidMarkdown children={msg.content} />
                                    </div>
                                </Show>
                            </div>
                        </div>
                    )}
                </For>
                <Show when={isLoading() && messages()[messages().length - 1]?.content === ''}>
                    <div class="flex justify-start mb-4">
                        <div class="bg-gray-700 text-gray-100 rounded-2xl rounded-bl-none px-4 py-2 animate-pulse">
                            Thinking...
                        </div>
                    </div>
                </Show>
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSubmit} class="flex gap-2">
                <input
                    type="text"
                    value={input()}
                    onInput={(e) => setInput(e.currentTarget.value)}
                    placeholder="Ask anything..."
                    class="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all shadow-lg"
                    disabled={isLoading()}
                />
                <button
                    type="submit"
                    disabled={isLoading()}
                    class="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:opacity-90 transition-all disabled:opacity-50 shadow-lg"
                >
                    Send
                </button>
            </form>
        </div>
    );
}

export default App;
