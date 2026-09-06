import type { TokenProvider } from "./TokenProvider.js";
export declare class StaticTokenProvider implements TokenProvider {
    private readonly _token;
    constructor(token: string);
    getToken(): Promise<string>;
}
