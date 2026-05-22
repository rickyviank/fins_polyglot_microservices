FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY target/account-service-*.jar app.jar
EXPOSE 8083
ENTRYPOINT ["java","-jar","/app/app.jar"]
