"use client";
import { signIn, signOut, useSession } from "next-auth/react";
import classNames from "classnames";

export default function AuthButton() {
  const { data: session, status } = useSession();

  const handleSignIn = () => signIn("google");
  const handleSignOut = () => signOut();

  if (status === "loading") {
    return <button className={classNames("px-4 py-2 rounded bg-gray-200 animate-pulse")}>Loading...</button>;
  }

  if (session) {
    return (
      <div className="flex flex-col items-center gap-2">
        <span className="text-sm text-gray-700">Signed in as {session.user?.email}</span>
        <button
          className={classNames(
            "px-4 py-2 rounded text-white transition",
            "bg-red-500 hover:bg-red-600"
          )}
          onClick={handleSignOut}
        >
          Sign out
        </button>
      </div>
    );
  }
  return (
    <button
      className={classNames(
        "px-4 py-2 rounded text-white transition",
        "bg-blue-600 hover:bg-blue-700"
      )}
      onClick={handleSignIn}
    >
      Sign in with Google
    </button>
  );
} 