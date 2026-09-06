import type { CreateTokenResponse } from "../../api/index.mjs";
import type { TokenProvider } from "./TokenProvider.mjs";
export type TokenCallback = (opts: {
    externalUserId: string;
}) => Promise<CreateTokenResponse>;
export declare class ConnectTokenProvider implements TokenProvider {
    private readonly _tokenCallback;
    private _externalUserId?;
    private _token?;
    private _tokenExpiresAt?;
    private _tokenRequest?;
    constructor({ tokenCallback, externalUserId }: {
        tokenCallback: TokenCallback;
        externalUserId: string;
    });
    get externalUserId(): string | undefined;
    getToken(): Promise<string>;
    refresh(): void;
}
