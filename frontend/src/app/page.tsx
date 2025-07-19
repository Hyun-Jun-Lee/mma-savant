import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-red-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold text-red-600">
            🥊 MMA Savant
          </CardTitle>
          <CardDescription className="text-lg">
            Your Personal MMA Expert Chat Assistant
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2 justify-center">
            <Badge variant="secondary">Fighters</Badge>
            <Badge variant="secondary">Techniques</Badge>
            <Badge variant="secondary">Events</Badge>
            <Badge variant="secondary">History</Badge>
          </div>
          
          <div className="space-y-2">
            <Button className="w-full bg-red-600 hover:bg-red-700" size="lg">
              Start Chat
            </Button>
            <Button variant="outline" className="w-full" size="lg">
              Sign in with Google
            </Button>
          </div>
          
          <div className="text-center text-sm text-gray-600">
            <p>Get expert insights on MMA fighters, techniques, and fight analysis</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
