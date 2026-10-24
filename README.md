    ~~~~~~~~~~How our SaaS will work~~~~~~~~~~~~~
       CUSTOMERS / DEVELOPERS
                 |
                 v
       Runtime RCA Website
                 |
         Sign up / Log in
                 |
                 v
        Register Application
                 |
                 v
        Get Application API Key
                 |
                 v
       Integrate Our Python SDK
                 |
                 v
      Their App Sends Error Events
                 |
                 v
       Our Platform Processes Them
                 |
                 v
          RCA Investigation
                 |
                 v
       Root Cause + Evidence + Fix
                 |
                 v
       Customer Views Dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
              Final architecture
                        |

             APPLICATIONS WE MONITOR
          Python / Django / Node.js / Java
                       |
                       v
                Runtime SDKs
                       |
                       v
              API Gateway / Ingestion
                       |
                       v
                Django REST API
                       |
             +---------+----------+
             |                    |
             v                    v
       PostgreSQL             Redis Queue
       Persistent Data             |
                                   v
                            Celery Workers
                                   |
                                   v
                         Event Processing Pipeline
                                   |
                  +----------------+----------------+
                  |                |                |
                  v                v                v
             Fingerprinting   Evidence Engine   Telemetry
                  |                |             Analysis
                  +----------------+----------------+
                                   |
                                   v
                              RCA Engine
                                   |
                         +---------+---------+
                         |                   |
                         v                   v
                   Rule-Based RCA       AI + RAG
                         |                   |
                         +---------+---------+
                                   |
                                   v
                              RCA Reports
                                   |
                                   v
                              PostgreSQL
                                   |
                                   v
                            Django REST API
                                   |
                                   v
                          React Dashboard
