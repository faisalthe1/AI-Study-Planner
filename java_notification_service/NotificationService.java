// NotificationService.java
import java.io.*;
import java.net.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Timer;
import java.util.TimerTask;
import org.json.JSONArray;
import org.json.JSONObject;

public class NotificationService {
    private static final String API_URL = "http://localhost:8000/api/upcoming-tasks/";
    private static final int CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes
    
    public static void main(String[] args) {
        Timer timer = new Timer();
        timer.scheduleAtFixedRate(new TimerTask() {
            @Override
            public void run() {
                checkForUpcomingTasks();
            }
        }, 0, CHECK_INTERVAL);
    }
    
    private static void checkForUpcomingTasks() {
        try {
            URL url = new URL(API_URL);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            
            int responseCode = conn.getResponseCode();
            if (responseCode == HttpURLConnection.HTTP_OK) {
                BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                String inputLine;
                StringBuilder response = new StringBuilder();
                
                while ((inputLine = in.readLine()) != null) {
                    response.append(inputLine);
                }
                in.close();
                
                JSONArray tasks = new JSONArray(response.toString());
                processTasks(tasks);
            } else {
                System.out.println("GET request failed. Response code: " + responseCode);
            }
        } catch (Exception e) {
            System.out.println("Error checking for tasks: " + e.getMessage());
        }
    }
    
    private static void processTasks(JSONArray tasks) {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss");
        LocalDateTime now = LocalDateTime.now();
        
        for (int i = 0; i < tasks.length(); i++) {
            JSONObject task = tasks.getJSONObject(i);
            String dueDateStr = task.getString("due_date");
            LocalDateTime dueDate = LocalDateTime.parse(dueDateStr.substring(0, 19), formatter);
            
            // Check if task is due within the next 24 hours
            if (dueDate.isAfter(now) && dueDate.isBefore(now.plusHours(24))) {
                String title = task.getString("title");
                String message = "Reminder: Task '" + title + "' is due on " + 
                                dueDate.format(DateTimeFormatter.ofPattern("MMM dd, yyyy HH:mm"));
                
                sendNotification(message);
            }
        }
    }
    
    private static void sendNotification(String message) {
        // This is a platform-independent notification method
        // For system notifications, you might use JavaFX Notifications or a library like Notifications for Java
        // For this example, we'll just print to console and could send email if configured
        
        System.out.println("NOTIFICATION: " + message);
        
        // Example of sending email (would need to configure SMTP settings)
        // sendEmailNotification(message);
    }
}