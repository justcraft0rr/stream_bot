"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConnectTokenProvider = void 0;
class ConnectTokenProvider {
    constructor({ tokenCallback, externalUserId }) {
        if (!externalUserId) {
            throw new Error("The external user ID cannot be blank");
        }
        if (typeof tokenCallback !== "function") {
            throw new Error("The token callback must be a function");
        }
        this._externalUserId = externalUserId;
        this._tokenCallback = tokenCallback;
    }
    get externalUserId() {
        return this._externalUserId;
    }
    getToken() {
        return __awaiter(this, void 0, void 0, function* () {
            if (this._token && this._tokenExpiresAt && this._tokenExpiresAt > new Date()) {
                return this._token;
            }
            if (this._tokenRequest) {
                return this._tokenRequest;
            }
            const tokenCallback = this._tokenCallback;
            const externalUserId = this._externalUserId;
            if (!tokenCallback) {
                throw new Error("No token callback provided");
            }
            if (!externalUserId) {
                throw new Error("No external user ID provided");
            }
            // Ensure only one token request is in-flight at a time.
            this._tokenRequest = (() => __awaiter(this, void 0, void 0, function* () {
                const { token, expiresAt } = yield tokenCallback({
                    externalUserId,
                });
                this._token = token;
                this._tokenExpiresAt = expiresAt;
                this._tokenRequest = undefined;
                return token;
            }))();
            return this._tokenRequest;
        });
    }
    refresh() {
        this._token = undefined;
    }
}
exports.ConnectTokenProvider = ConnectTokenProvider;
