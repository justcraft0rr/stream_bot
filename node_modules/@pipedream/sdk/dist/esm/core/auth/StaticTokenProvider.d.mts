import type { TokenProvider } from "./TokenProvider.mjs";
export declare class StaticTokenProvider implements TokenProvider {
    private readonly _token;
    constructor(token: string);
    getToken(): Promise<string>;
}
