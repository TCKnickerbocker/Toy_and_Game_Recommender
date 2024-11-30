import {
  ClerkProvider,
  SignInButton,
  SignedIn,
  SignedOut,
  UserButton,
} from "@clerk/nextjs";
// import NewUserPage from "./welcome/new_user/page";
// import WelcomeBackPage from "./welcome/back/page";

export default function Page() {
  return (
    <ClerkProvider>
      <SignedOut>
        <SignInButton />
      </SignedOut>
      <SignedIn>
        <UserButton />
      </SignedIn>
    </ClerkProvider>
  );
}
